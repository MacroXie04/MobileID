import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import {
  checkAuthenticationError,
  refreshToken,
  isRefreshing,
} from '@shared/utils/tokenRefresh.js';

// Mock dependencies
vi.mock('@app/config/config', () => ({
  baseURL: 'http://localhost:8000',
}));

const mockGetRefreshToken = vi.fn();
const mockSetAuthTokens = vi.fn();

vi.mock('@shared/api/axios', () => ({
  getRefreshToken: () => mockGetRefreshToken(),
  setAuthTokens: (tokens) => mockSetAuthTokens(tokens),
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

    it('should detect 403 status', () => {
      const response = { status: 403 };
      expect(checkAuthenticationError({}, response)).toBe(true);
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
    it('should return false immediately if no refresh token available', async () => {
      mockGetRefreshToken.mockReturnValue(null);

      const result = await refreshToken();

      expect(result).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should return false for empty refresh token', async () => {
      mockGetRefreshToken.mockReturnValue('');

      const result = await refreshToken();

      expect(result).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should make POST request to token refresh endpoint', async () => {
      mockGetRefreshToken.mockReturnValue('valid-refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ access: 'new-access', refresh: 'new-refresh' }),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/authn/token/refresh/',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: 'valid-refresh-token' }),
        })
      );
    });

    it('should update tokens via setAuthTokens on success', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ access: 'new-access-token', refresh: 'new-refresh-token' }),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(true);
      expect(mockSetAuthTokens).toHaveBeenCalledWith({
        access: 'new-access-token',
        refresh: 'new-refresh-token',
      });
    });

    it('should use original refresh token if new one not provided', async () => {
      mockGetRefreshToken.mockReturnValue('original-refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ access: 'new-access-token' }), // No refresh in response
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      await promise;

      expect(mockSetAuthTokens).toHaveBeenCalledWith({
        access: 'new-access-token',
        refresh: 'original-refresh-token',
      });
    });

    it('should return false on 401 response', async () => {
      mockGetRefreshToken.mockReturnValue('expired-refresh-token');
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
      expect(mockSetAuthTokens).not.toHaveBeenCalled();
    });

    it('should return false on 403 response', async () => {
      mockGetRefreshToken.mockReturnValue('invalid-refresh-token');
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
      mockGetRefreshToken.mockReturnValue('refresh-token');
      global.fetch.mockRejectedValue(new Error('Network error'));

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(false);
    });

    it('should handle non-JSON response gracefully', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'text/html' }, // Not JSON
        json: () => Promise.reject(new Error('Not JSON')),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      // Should return false because data.access won't exist
      expect(result).toBe(false);
    });

    it('should handle JSON parse error gracefully', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      const promise = refreshToken();
      await vi.runAllTimersAsync();
      const result = await promise;

      // Should return false because data will be null
      expect(result).toBe(false);
    });

    it('should reuse in-flight refresh promise (prevent duplicate requests)', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');

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
        json: () => Promise.resolve({ access: 'new-access', refresh: 'new-refresh' }),
      });

      await vi.runAllTimersAsync();

      const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3]);

      expect(result1).toBe(true);
      expect(result2).toBe(true);
      expect(result3).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should clear activeRefreshTokenPromise after completion', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ access: 'access', refresh: 'refresh' }),
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

    it('should timeout waiting for in-flight refresh after 10 seconds', async () => {
      mockGetRefreshToken.mockReturnValue('refresh-token');

      // First call: never resolving fetch
      const neverResolvingFetch = new Promise(() => {}); // Never resolves
      global.fetch.mockReturnValue(neverResolvingFetch);

      // Start first refresh (will hang)
      const promise1 = refreshToken();

      // Second call should wait then timeout
      const promise2 = refreshToken();

      // Advance timer by 10 seconds
      await vi.advanceTimersByTimeAsync(10000);

      // The waiting promise should have timed out and returned false
      const result2 = await promise2;
      expect(result2).toBe(false);
    });
  });

  describe('isRefreshing', () => {
    it('should return false when no refresh token available', async () => {
      // When no refresh token, should not start refreshing
      mockGetRefreshToken.mockReturnValue(null);
      const result = await refreshToken();
      expect(result).toBe(false);
    });

    it('should expose isRefreshing function', () => {
      // Basic test that the function exists and returns a boolean
      expect(typeof isRefreshing).toBe('function');
      expect(typeof isRefreshing()).toBe('boolean');
    });
  });
});
