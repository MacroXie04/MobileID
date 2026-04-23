import { beforeEach, describe, expect, it, vi } from 'vitest';

// Mock dependencies
const mockRouterPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockRouterPush }),
}));

const mockClearAuthCookies = vi.fn();
const mockClearAuthStorage = vi.fn();
vi.mock('@shared/utils/cookie', () => ({
  clearAuthCookies: () => mockClearAuthCookies(),
  clearAuthStorage: () => mockClearAuthStorage(),
}));

const mockCheckAuthenticationError = vi.fn();
const mockRefreshToken = vi.fn();
vi.mock('@shared/utils/tokenRefresh', () => ({
  checkAuthenticationError: (...args) => mockCheckAuthenticationError(...args),
  refreshToken: () => mockRefreshToken(),
}));

vi.mock('@user/composables/useUserInfo', () => ({
  clearUserProfile: vi.fn(),
}));

import { useToken } from '@auth/composables/useToken';

describe('useToken', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    window.isLoggingOut = false;
  });

  afterEach(() => {
    vi.useRealTimers();
    window.isLoggingOut = false;
  });

  describe('checkAuthenticationError', () => {
    it('should delegate to shared checkAuthenticationError', () => {
      const { checkAuthenticationError } = useToken();
      const data = { code: 'token_not_valid' };
      const response = { status: 401 };

      mockCheckAuthenticationError.mockReturnValue(true);
      const result = checkAuthenticationError(data, response);

      expect(mockCheckAuthenticationError).toHaveBeenCalledWith(data, response);
      expect(result).toBe(true);
    });
  });

  describe('refreshToken', () => {
    it('should set isRefreshingToken during refresh', async () => {
      let resolveRefresh;
      mockRefreshToken.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveRefresh = resolve;
          })
      );

      const { refreshToken, isRefreshingToken } = useToken();
      const promise = refreshToken();

      expect(isRefreshingToken.value).toBe(true);

      resolveRefresh(true);
      await promise;

      expect(isRefreshingToken.value).toBe(false);
    });

    it('should reset isRefreshingToken even on error', async () => {
      mockRefreshToken.mockRejectedValue(new Error('Refresh failed'));

      const { refreshToken, isRefreshingToken } = useToken();
      await expect(refreshToken()).rejects.toThrow('Refresh failed');
      expect(isRefreshingToken.value).toBe(false);
    });
  });

  describe('handleTokenExpired', () => {
    it('should return true if token refresh succeeds', async () => {
      mockRefreshToken.mockResolvedValue(true);

      const { handleTokenExpired } = useToken();
      const result = await handleTokenExpired();

      expect(result).toBe(true);
      expect(window.isLoggingOut).toBe(false);
    });

    it('should clear auth and redirect on refresh failure', async () => {
      mockRefreshToken.mockResolvedValue(false);

      const { handleTokenExpired } = useToken();
      const result = await handleTokenExpired();

      expect(result).toBe(false);
      expect(mockClearAuthCookies).toHaveBeenCalled();
      expect(mockClearAuthStorage).toHaveBeenCalled();

      // Advance past redirect timeout
      vi.advanceTimersByTime(100);
      expect(mockRouterPush).toHaveBeenCalledWith('/login');
    });

    it('should not run if already logging out', async () => {
      window.isLoggingOut = true;

      const { handleTokenExpired } = useToken();
      const result = await handleTokenExpired();

      expect(result).toBeUndefined();
      expect(mockRefreshToken).not.toHaveBeenCalled();
    });

    it('should clear auth and redirect on refresh exception', async () => {
      mockRefreshToken.mockRejectedValue(new Error('Network error'));

      const { handleTokenExpired } = useToken();
      const result = await handleTokenExpired();

      expect(result).toBe(false);
      expect(mockClearAuthCookies).toHaveBeenCalled();
      expect(mockClearAuthStorage).toHaveBeenCalled();
    });

    it('should reset isLoggingOut flag after timeout', async () => {
      mockRefreshToken.mockResolvedValue(false);

      const { handleTokenExpired } = useToken();
      await handleTokenExpired();

      vi.advanceTimersByTime(1000);
      expect(window.isLoggingOut).toBe(false);
    });
  });
});
