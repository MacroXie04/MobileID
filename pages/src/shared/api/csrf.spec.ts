import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ensureCsrfToken } from '@shared/api/csrf';

vi.mock('@shared/config/config', () => ({
  baseURL: 'https://api.example.com',
}));

const mockGetCookie = vi.fn();
vi.mock('@shared/utils/cookie', () => ({
  getCookie: (...args) => mockGetCookie(...args),
}));

describe('ensureCsrfToken', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    delete global.fetch;
  });

  it('should return existing cookie without making a request', async () => {
    mockGetCookie.mockReturnValue('existing-token');

    const token = await ensureCsrfToken();

    expect(token).toBe('existing-token');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('should fetch CSRF token when no cookie exists', async () => {
    mockGetCookie
      .mockReturnValueOnce(null) // initial check
      .mockReturnValueOnce('fetched-token'); // after fetch sets cookie

    global.fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'text/html' },
    });

    const token = await ensureCsrfToken();

    expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/authn/csrf/', {
      method: 'GET',
      credentials: 'include',
    });
    expect(token).toBe('fetched-token');
  });

  it('should fall back to JSON response body for token', async () => {
    mockGetCookie
      .mockReturnValueOnce(null) // initial check
      .mockReturnValueOnce(null) // after fetch, no cookie
      .mockReturnValueOnce(null); // inside json handler

    global.fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve({ csrfToken: 'json-token' }),
    });

    const token = await ensureCsrfToken();

    expect(token).toBe('json-token');
  });

  it('should return empty string on fetch error', async () => {
    mockGetCookie.mockReturnValue(null);
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    const token = await ensureCsrfToken();

    expect(token).toBe('');
  });

  it('should return empty string for non-JSON response with no cookie', async () => {
    mockGetCookie.mockReturnValue(null);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'text/html' },
    });

    const token = await ensureCsrfToken();

    expect(token).toBe('');
  });

  it('should handle JSON parse error gracefully', async () => {
    mockGetCookie
      .mockReturnValueOnce(null) // initial
      .mockReturnValueOnce(null) // after fetch
      .mockReturnValueOnce(null); // inside catch

    global.fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.reject(new Error('Invalid JSON')),
    });

    const token = await ensureCsrfToken();

    expect(token).toBe('');
  });

  it('should deduplicate concurrent requests', async () => {
    let resolveFirst;
    mockGetCookie
      .mockReturnValueOnce(null) // first call initial check
      .mockReturnValueOnce(null) // second call initial check
      .mockReturnValue('shared-token'); // after fetch

    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFirst = resolve;
        })
    );

    const promise1 = ensureCsrfToken();
    const promise2 = ensureCsrfToken();

    // Only one fetch should be made
    expect(global.fetch).toHaveBeenCalledTimes(1);

    resolveFirst({
      ok: true,
      headers: { get: () => 'text/html' },
    });

    const [token1, token2] = await Promise.all([promise1, promise2]);
    expect(token1).toBe('shared-token');
    expect(token2).toBe('shared-token');
  });
});
