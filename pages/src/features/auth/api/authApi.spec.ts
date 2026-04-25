import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  establishAuthenticatedSession,
  login,
  userInfo,
  logout,
  register,
} from '@auth/api/authApi';
import { ApiError } from '@shared/api/client';

// Mock dependencies
const mockApiRequest = vi.fn();
vi.mock('@shared/api/client', () => ({
  ApiError: class ApiError extends Error {
    constructor(message, status, data) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.data = data;
    }
  },
  apiRequest: (...args) => mockApiRequest(...args),
}));

const mockClearAuthCookies = vi.fn();
const mockClearAuthStorage = vi.fn();
vi.mock('@shared/utils/cookie', () => ({
  clearAuthCookies: () => mockClearAuthCookies(),
  clearAuthStorage: () => mockClearAuthStorage(),
}));

const mockRefreshToken = vi.fn();
vi.mock('./tokenRefresh', () => ({
  refreshToken: () => mockRefreshToken(),
}));

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should call login endpoint with username and password', async () => {
      mockApiRequest.mockResolvedValueOnce({ message: 'Login successful' });

      const result = await login('testuser', 'password123');

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/login/', {
        method: 'POST',
        body: { username: 'testuser', password: 'password123' },
      });
      expect(result).toEqual({ message: 'Login successful' });
    });

    it('should not store tokens locally (cookie-only auth)', async () => {
      mockApiRequest.mockResolvedValueOnce({ message: 'Login successful' });

      await login('user', 'pass');

      // No localStorage interaction expected
      expect(mockClearAuthCookies).not.toHaveBeenCalled();
    });

    it('should throw ApiError with detail for auth errors', async () => {
      const apiError = new ApiError('Error', 401, { detail: 'Custom error message' });
      mockApiRequest.mockRejectedValueOnce(apiError);

      try {
        await login('user', 'pass');
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error.message).toBe('Custom error message');
        expect(error.data.detail).toBe('Custom error message');
      }
    });

    it('should use default message when no detail provided', async () => {
      const apiError = new ApiError('Error', 401, {});
      mockApiRequest.mockRejectedValueOnce(apiError);

      try {
        await login('user', 'pass');
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error.message).toBe('Invalid username or password.');
      }
    });

    it('should re-throw non-ApiError errors', async () => {
      const networkError = new Error('Network failure');
      mockApiRequest.mockRejectedValueOnce(networkError);

      await expect(login('user', 'pass')).rejects.toThrow('Network failure');
    });
  });

  describe('userInfo', () => {
    it('should call apiRequest with user_info endpoint', async () => {
      const mockUser = { id: 1, username: 'testuser' };
      mockApiRequest.mockResolvedValue(mockUser);

      const result = await userInfo();

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/user_info/');
      expect(result).toEqual(mockUser);
    });

    it('should return null on ApiError', async () => {
      const apiError = new ApiError('Not found', 404, {});
      mockApiRequest.mockRejectedValue(apiError);

      const result = await userInfo();

      expect(result).toBeNull();
    });

    it('should re-throw non-ApiError errors', async () => {
      const networkError = new Error('Network error');
      mockApiRequest.mockRejectedValue(networkError);

      await expect(userInfo()).rejects.toThrow('Network error');
    });
  });

  describe('establishAuthenticatedSession', () => {
    it('should return the current user when session is already available', async () => {
      const mockUser = { id: 1, username: 'testuser' };
      mockApiRequest.mockResolvedValueOnce(mockUser);

      const result = await establishAuthenticatedSession();

      expect(result).toEqual(mockUser);
      expect(mockRefreshToken).not.toHaveBeenCalled();
    });

    it('should refresh once when the first session lookup returns unauthenticated', async () => {
      const mockUser = { id: 1, username: 'testuser' };
      mockApiRequest
        .mockRejectedValueOnce(new ApiError('Unauthorized', 401, {}))
        .mockResolvedValueOnce(mockUser);
      mockRefreshToken.mockResolvedValueOnce(true);

      const result = await establishAuthenticatedSession();

      expect(mockRefreshToken).toHaveBeenCalledTimes(1);
      expect(mockApiRequest).toHaveBeenNthCalledWith(1, '/authn/user_info/');
      expect(mockApiRequest).toHaveBeenNthCalledWith(2, '/authn/user_info/');
      expect(result).toEqual(mockUser);
    });

    it('should return null when refresh cannot restore the session', async () => {
      mockApiRequest.mockRejectedValueOnce(new ApiError('Unauthorized', 401, {}));
      mockRefreshToken.mockResolvedValueOnce(false);

      const result = await establishAuthenticatedSession();

      expect(mockRefreshToken).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
    });

    it('should re-throw server errors from the initial session lookup', async () => {
      mockApiRequest.mockRejectedValueOnce(new ApiError('Server error', 500, {}));

      await expect(establishAuthenticatedSession()).rejects.toThrow('Server error');
      expect(mockRefreshToken).not.toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should call apiRequest with logout endpoint', async () => {
      mockApiRequest.mockResolvedValue({});

      await logout();

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/logout/', { method: 'POST' });
    });

    it('should clear auth cookies and storage even on success', async () => {
      mockApiRequest.mockResolvedValue({});

      await logout();

      expect(mockClearAuthCookies).toHaveBeenCalled();
      expect(mockClearAuthStorage).toHaveBeenCalled();
    });

    it('should clear auth cookies and storage even on error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Server error'));

      await logout();

      expect(mockClearAuthCookies).toHaveBeenCalled();
      expect(mockClearAuthStorage).toHaveBeenCalled();
    });

    it('should not throw on API error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Server error'));

      // Should not throw
      await expect(logout()).resolves.toBeUndefined();
    });
  });

  describe('register', () => {
    it('should call apiRequest with register endpoint and user data', async () => {
      const userData = { username: 'newuser', password: 'pass123', name: 'New User' };
      mockApiRequest.mockResolvedValue({ success: true, message: 'Registration successful' });

      const result = await register(userData);

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/register/', {
        method: 'POST',
        body: userData,
      });
      expect(result).toEqual({ success: true, message: 'Registration successful' });
    });

    it('should not store tokens locally (cookie-only auth)', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      mockApiRequest.mockResolvedValue({ success: true });

      await register(userData);

      // No localStorage interaction expected
      expect(mockClearAuthCookies).not.toHaveBeenCalled();
    });

    it('should logout and retry if token_not_valid error', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const tokenError = new ApiError('Token error', 401, { code: 'token_not_valid' });
      mockApiRequest
        .mockRejectedValueOnce(tokenError) // First register fails
        .mockResolvedValueOnce({}) // logout succeeds
        .mockResolvedValueOnce({ success: true }); // Retry succeeds

      const result = await register(userData);

      expect(mockClearAuthCookies).toHaveBeenCalled(); // logout clears cookies
      expect(mockClearAuthStorage).toHaveBeenCalled(); // logout clears storage
      expect(mockApiRequest).toHaveBeenCalledTimes(3); // register, logout, register retry
      expect(result).toEqual({ success: true });
    });

    it('should logout and retry if token is expired error', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const tokenError = new ApiError('Token error', 401, { detail: 'Token is expired' });
      mockApiRequest
        .mockRejectedValueOnce(tokenError)
        .mockResolvedValueOnce({}) // logout
        .mockResolvedValueOnce({ success: true }); // retry

      await register(userData);

      expect(mockClearAuthCookies).toHaveBeenCalled();
      expect(mockClearAuthStorage).toHaveBeenCalled();
    });

    it('should re-throw non-token errors', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const validationError = new ApiError('Validation error', 400, {
        username: 'Already exists',
      });
      mockApiRequest.mockRejectedValue(validationError);

      await expect(register(userData)).rejects.toThrow();
    });

    it('should re-throw if retry also fails', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const tokenError = new ApiError('Token error', 401, { code: 'token_not_valid' });
      const retryError = new ApiError('Still failing', 400, {});
      mockApiRequest
        .mockRejectedValueOnce(tokenError)
        .mockResolvedValueOnce({}) // logout
        .mockRejectedValueOnce(retryError); // retry fails

      await expect(register(userData)).rejects.toThrow();
    });
  });
});
