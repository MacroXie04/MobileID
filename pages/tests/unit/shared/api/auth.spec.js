import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  fetchLoginChallenge,
  login,
  userInfo,
  logout,
  getUserProfile,
  updateUserProfile,
  register,
} from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client.js';

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

const mockEncryptPassword = vi.fn();
const mockClearPublicKeyCache = vi.fn();
vi.mock('@shared/utils/encryption', () => ({
  encryptPassword: (...args) => mockEncryptPassword(...args),
  clearPublicKeyCache: () => mockClearPublicKeyCache(),
}));

const mockSetAuthTokens = vi.fn();
const mockClearAuthTokens = vi.fn();
vi.mock('@shared/api/axios', () => ({
  setAuthTokens: (tokens) => mockSetAuthTokens(tokens),
  clearAuthTokens: () => mockClearAuthTokens(),
}));

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchLoginChallenge', () => {
    it('should call apiRequest with login-challenge endpoint', async () => {
      const mockChallenge = { nonce: 'test-nonce', kid: 'key-1', public_key: 'pem-key' };
      mockApiRequest.mockResolvedValue(mockChallenge);

      const result = await fetchLoginChallenge();

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/login-challenge/');
      expect(result).toEqual(mockChallenge);
    });
  });

  describe('login', () => {
    it('should fetch challenge, encrypt password, and call login endpoint', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      mockApiRequest
        .mockResolvedValueOnce(mockChallenge) // fetchLoginChallenge
        .mockResolvedValueOnce({ access: 'access-token', refresh: 'refresh-token' }); // login
      mockEncryptPassword.mockResolvedValue('encrypted-password');

      const result = await login('testuser', 'password123');

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/login-challenge/');
      expect(mockEncryptPassword).toHaveBeenCalledWith('password123', mockChallenge);
      expect(mockApiRequest).toHaveBeenCalledWith('/authn/login/', {
        method: 'POST',
        body: { username: 'testuser', password: 'encrypted-password' },
      });
      expect(result).toEqual({ access: 'access-token', refresh: 'refresh-token' });
    });

    it('should save tokens to localStorage on success', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      mockApiRequest
        .mockResolvedValueOnce(mockChallenge)
        .mockResolvedValueOnce({ access: 'new-access', refresh: 'new-refresh' });
      mockEncryptPassword.mockResolvedValue('encrypted');

      await login('user', 'pass');

      expect(mockSetAuthTokens).toHaveBeenCalledWith({
        access: 'new-access',
        refresh: 'new-refresh',
      });
    });

    it('should not save tokens if response has no tokens', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      mockApiRequest
        .mockResolvedValueOnce(mockChallenge)
        .mockResolvedValueOnce({ message: 'Login successful' }); // No tokens
      mockEncryptPassword.mockResolvedValue('encrypted');

      await login('user', 'pass');

      expect(mockSetAuthTokens).not.toHaveBeenCalled();
    });

    it('should clear public key cache on 401 error', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      const apiError = new ApiError('Invalid credentials', 401, { detail: 'Bad password' });
      mockApiRequest.mockResolvedValueOnce(mockChallenge).mockRejectedValueOnce(apiError);
      mockEncryptPassword.mockResolvedValue('encrypted');

      await expect(login('user', 'pass')).rejects.toThrow();

      expect(mockClearPublicKeyCache).toHaveBeenCalled();
    });

    it('should clear public key cache on 410 error (key rotated)', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      const apiError = new ApiError('Key expired', 410, { detail: 'Key has been rotated' });
      mockApiRequest.mockResolvedValueOnce(mockChallenge).mockRejectedValueOnce(apiError);
      mockEncryptPassword.mockResolvedValue('encrypted');

      await expect(login('user', 'pass')).rejects.toThrow();

      expect(mockClearPublicKeyCache).toHaveBeenCalled();
    });

    it('should throw ApiError with detail for auth errors', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      const apiError = new ApiError('Error', 401, { detail: 'Custom error message' });
      mockApiRequest.mockResolvedValueOnce(mockChallenge).mockRejectedValueOnce(apiError);
      mockEncryptPassword.mockResolvedValue('encrypted');

      try {
        await login('user', 'pass');
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error.message).toBe('Custom error message');
        expect(error.data.detail).toBe('Custom error message');
      }
    });

    it('should use default message when no detail provided', async () => {
      const mockChallenge = { nonce: 'nonce', kid: 'kid', public_key: 'key' };
      const apiError = new ApiError('Error', 401, {});
      mockApiRequest.mockResolvedValueOnce(mockChallenge).mockRejectedValueOnce(apiError);
      mockEncryptPassword.mockResolvedValue('encrypted');

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

  describe('logout', () => {
    it('should call apiRequest with logout endpoint', async () => {
      mockApiRequest.mockResolvedValue({});

      await logout();

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/logout/', { method: 'POST' });
    });

    it('should clear auth tokens even on success', async () => {
      mockApiRequest.mockResolvedValue({});

      await logout();

      expect(mockClearAuthTokens).toHaveBeenCalled();
    });

    it('should clear auth tokens even on error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Server error'));

      await logout();

      expect(mockClearAuthTokens).toHaveBeenCalled();
    });

    it('should not throw on API error', async () => {
      mockApiRequest.mockRejectedValue(new Error('Server error'));

      // Should not throw
      await expect(logout()).resolves.toBeUndefined();
    });
  });

  describe('getUserProfile', () => {
    it('should call apiRequest with profile endpoint', async () => {
      const mockProfile = { name: 'Test User', avatar: 'url' };
      mockApiRequest.mockResolvedValue(mockProfile);

      const result = await getUserProfile();

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/profile/');
      expect(result).toEqual(mockProfile);
    });
  });

  describe('updateUserProfile', () => {
    it('should call apiRequest with PUT method and profile data', async () => {
      const profileData = { name: 'New Name' };
      mockApiRequest.mockResolvedValue({ success: true });

      await updateUserProfile(profileData);

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/profile/', {
        method: 'PUT',
        body: profileData,
      });
    });
  });

  describe('register', () => {
    it('should call apiRequest with register endpoint and user data', async () => {
      const userData = { username: 'newuser', password: 'pass123', name: 'New User' };
      mockApiRequest.mockResolvedValue({ access: 'token', refresh: 'refresh' });

      const result = await register(userData);

      expect(mockApiRequest).toHaveBeenCalledWith('/authn/register/', {
        method: 'POST',
        body: userData,
      });
      expect(result).toEqual({ access: 'token', refresh: 'refresh' });
    });

    it('should save tokens to localStorage on success', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      mockApiRequest.mockResolvedValue({ access: 'new-access', refresh: 'new-refresh' });

      await register(userData);

      expect(mockSetAuthTokens).toHaveBeenCalledWith({
        access: 'new-access',
        refresh: 'new-refresh',
      });
    });

    it('should not save tokens if response has no tokens', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      mockApiRequest.mockResolvedValue({ message: 'Registered' });

      await register(userData);

      expect(mockSetAuthTokens).not.toHaveBeenCalled();
    });

    it('should logout and retry if token_not_valid error', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const tokenError = new ApiError('Token error', 401, { code: 'token_not_valid' });
      mockApiRequest
        .mockRejectedValueOnce(tokenError) // First register fails
        .mockResolvedValueOnce({}) // logout succeeds
        .mockResolvedValueOnce({ access: 'token', refresh: 'refresh' }); // Retry succeeds

      const result = await register(userData);

      expect(mockClearAuthTokens).toHaveBeenCalled(); // logout clears tokens
      expect(mockApiRequest).toHaveBeenCalledTimes(3); // register, logout, register retry
      expect(result).toEqual({ access: 'token', refresh: 'refresh' });
    });

    it('should logout and retry if token is expired error', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const tokenError = new ApiError('Token error', 401, { detail: 'Token is expired' });
      mockApiRequest
        .mockRejectedValueOnce(tokenError)
        .mockResolvedValueOnce({}) // logout
        .mockResolvedValueOnce({ success: true }); // retry

      await register(userData);

      expect(mockClearAuthTokens).toHaveBeenCalled();
    });

    it('should re-throw non-token errors', async () => {
      const userData = { username: 'newuser', password: 'pass' };
      const validationError = new ApiError('Validation error', 400, { username: 'Already exists' });
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
