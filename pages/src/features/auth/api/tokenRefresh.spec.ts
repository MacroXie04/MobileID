import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { checkAuthenticationError, refreshToken, isRefreshing } from '@auth/api/tokenRefresh';

// Mock dependencies
vi.mock('@shared/config/config', () => ({
  baseURL: 'http://localhost:8000',
}));
vi.mock('@auth/state/authState', () => ({
  invalidateUserInfoCache: vi.fn(),
}));

describe('tokenRefresh utils', () => {
  let originalFetch;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    originalFetch = global.fetch;
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    global.fetch = originalFetch;
  });

  describe('checkAuthenticationError', () => {
    it('should detect code === "token_not_valid"', () => {
      const data = { code: 'token_not_valid' };
      expect(checkAuthenticationError(data, {})).toBe(true);
    });

    it('should detect detail containing "token not valid"', () => {
      const data = { detail: 'This token not valid anymore' };
      expect(checkAuthenticationError(data, {})).toBe(true);
    });

    it('should detect detail containing "Token is expired"', () => {
      const data = { detail: 'Token is expired' };
      expect(checkAuthenticationError(data, {})).toBe(true);
    });

    it('should detect detail containing "Invalid token"', () => {
      const data = { detail: 'Invalid token provided' };
      expect(checkAuthenticationError(data, {})).toBe(true);
    });

    it('should detect 401 status', () => {
      const response = { status: 401 };
      expect(checkAuthenticationError({}, response)).toBe(true);
    });

    it('should not detect 403 status as auth error (403 is authorization, not authentication)', () => {
      const response = { status: 403 };
      expect(checkAuthenticationError({}, response)).toBe(false);
    });

    it('should return false for 200 OK', () => {
      const response = { status: 200 };
      expect(checkAuthenticationError({}, response)).toBe(false);
    });

    it('should return false for empty data and response', () => {
      expect(checkAuthenticationError({}, {})).toBe(false);
    });

    it('should return false for null data', () => {
      expect(checkAuthenticationError(null, { status: 200 })).toBe(false);
    });

    it('should return false for undefined data', () => {
      expect(checkAuthenticationError(undefined, { status: 200 })).toBe(false);
    });

    it('should return false for 400 status (bad request, not auth error)', () => {
      const response = { status: 400 };
      expect(checkAuthenticationError({}, response)).toBe(false);
    });

    it('should return false for 500 status (server error, not auth error)', () => {
      const response = { status: 500 };
      expect(checkAuthenticationError({}, response)).toBe(false);
    });
  });

  describe('refreshToken', () => {
    it('should make POST request to token refresh endpoint with credentials', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/authn/token/refresh/',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        })
      );
      // Should NOT send a body (cookie-based refresh)
      expect(global.fetch.mock.calls[0][1].body).toBeUndefined();
    });

    it('should return true on successful refresh', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(true);
    });

    it('should return false on 401 response', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ code: 'token_not_valid' }),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(false);
    });

    it('should return false on 403 response', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 403,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ detail: 'Token is expired' }),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(false);
    });

    it('should return false on network error', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(false);
    });

    it('should handle non-JSON response gracefully', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'text/html' }, // Not JSON
        json: () => Promise.reject(new Error('Not JSON')),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      // Should return true because res.ok is true (cookie-based, no body check)
      expect(result).toBe(true);
    });

    it('should handle JSON parse error gracefully', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      // Should return true because res.ok is true
      expect(result).toBe(true);
    });

    it('should reuse in-flight refresh promise (prevent duplicate requests)', async () => {
      let resolveFirst;
      const firstFetchPromise = new Promise((resolve) => {
        resolveFirst = resolve;
      });

      global.fetch.mockReturnValue(firstFetchPromise);

      // Start first refresh
      const promise1 = refreshToken();
      const promise2 = refreshToken();
      const promise3 = refreshToken();

      // All should be waiting for the same promise
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Resolve the fetch
      resolveFirst({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await vi.runAllTimersAsync();

      const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3]);

      expect(result1).toBe(true);
      expect(result2).toBe(true);
      expect(result3).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should clear activeRefreshTokenPromise after completion', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      const promise1 = refreshToken();
      await vi.runAllTimersAsync();
      await promise1;

      // Start a new refresh - should make a new fetch call
      const promise2 = refreshToken();
      await vi.runAllTimersAsync();
      await promise2;

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('should share the same promise for concurrent callers (no timeout wrapper)', async () => {
      let resolveFirst;
      const firstFetchPromise = new Promise((resolve) => {
        resolveFirst = resolve;
      });

      global.fetch.mockReturnValue(firstFetchPromise);

      // Start first refresh
      const promise1 = refreshToken();
      // Second caller gets the exact same promise reference
      const promise2 = refreshToken();

      // Only one fetch should have been made
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Resolve the fetch — both callers should get the same result
      resolveFirst({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ code: 'token_not_valid' }),
      });

      await vi.runAllTimersAsync();

      const [result1, result2] = await Promise.all([promise1, promise2]);
      expect(result1).toBe(false);
      expect(result2).toBe(false);
    });
  });

  describe('isRefreshing', () => {
    it('should expose isRefreshing function', () => {
      // Basic test that the function exists and returns a boolean
      expect(typeof isRefreshing).toBe('function');
      expect(typeof isRefreshing()).toBe('boolean');
    });
  });
});
