import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiRequest } from '@shared/api/client.js';

// Mock dependencies
const mockEnsureCsrfToken = vi.fn();
vi.mock('@shared/api/csrf', () => ({
  ensureCsrfToken: () => mockEnsureCsrfToken(),
}));

const mockAxios = vi.fn();
vi.mock('@shared/api/axios', () => ({
  default: (config) => mockAxios(config),
}));

describe('API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockEnsureCsrfToken.mockResolvedValue('mock-csrf-token');
  });

  describe('ApiError', () => {
    it('should create error with message, status, and data', () => {
      const error = new ApiError('Something went wrong', 400, { field: 'Invalid' });

      expect(error.message).toBe('Something went wrong');
      expect(error.status).toBe(400);
      expect(error.data).toEqual({ field: 'Invalid' });
    });

    it('should have correct name property', () => {
      const error = new ApiError('Test error', 500, {});

      expect(error.name).toBe('ApiError');
    });

    it('should be an instance of Error', () => {
      const error = new ApiError('Test', 400, {});

      expect(error).toBeInstanceOf(Error);
    });
  });

  describe('apiRequest', () => {
    it('should call ensureCsrfToken for POST requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'POST' });

      expect(mockEnsureCsrfToken).toHaveBeenCalled();
    });

    it('should call ensureCsrfToken for PUT requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'PUT' });

      expect(mockEnsureCsrfToken).toHaveBeenCalled();
    });

    it('should call ensureCsrfToken for DELETE requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'DELETE' });

      expect(mockEnsureCsrfToken).toHaveBeenCalled();
    });

    it('should call ensureCsrfToken for PATCH requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'PATCH' });

      expect(mockEnsureCsrfToken).toHaveBeenCalled();
    });

    it('should NOT call ensureCsrfToken for GET requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'GET' });

      expect(mockEnsureCsrfToken).not.toHaveBeenCalled();
    });

    it('should NOT call ensureCsrfToken for HEAD requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'HEAD' });

      expect(mockEnsureCsrfToken).not.toHaveBeenCalled();
    });

    it('should NOT call ensureCsrfToken for OPTIONS requests', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'OPTIONS' });

      expect(mockEnsureCsrfToken).not.toHaveBeenCalled();
    });

    it('should default to GET method', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/');

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(mockEnsureCsrfToken).not.toHaveBeenCalled();
    });

    it('should pass headers from options', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', {
        method: 'GET',
        headers: { 'X-Custom-Header': 'value' },
      });

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: { 'X-Custom-Header': 'value' },
        })
      );
    });

    it('should pass body as data to axios', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', {
        method: 'POST',
        body: { username: 'test', password: 'pass' },
      });

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          data: { username: 'test', password: 'pass' },
        })
      );
    });

    it('should not include body in config (mapped to data)', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', {
        method: 'POST',
        body: { test: 'data' },
      });

      const callConfig = mockAxios.mock.calls[0][0];
      expect(callConfig.body).toBeUndefined();
      expect(callConfig.data).toEqual({ test: 'data' });
    });

    it('should set withCredentials based on options (true)', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', {
        method: 'GET',
        withCredentials: true,
      });

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          withCredentials: true,
        })
      );
    });

    it('should set withCredentials based on options (false)', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', {
        method: 'GET',
        withCredentials: false,
      });

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          withCredentials: false,
        })
      );
    });

    it('should default withCredentials to true', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/test/', { method: 'GET' });

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          withCredentials: true,
        })
      );
    });

    it('should return response.data on success', async () => {
      const responseData = { id: 1, name: 'Test' };
      mockAxios.mockResolvedValue({ data: responseData });

      const result = await apiRequest('/api/test/');

      expect(result).toEqual(responseData);
    });

    it('should throw ApiError with status and data on HTTP error', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Bad request', errors: { field: 'Invalid' } },
        },
      };
      mockAxios.mockRejectedValue(errorResponse);

      await expect(apiRequest('/api/test/', { method: 'POST' })).rejects.toThrow(ApiError);

      try {
        await apiRequest('/api/test/', { method: 'POST' });
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect(error.status).toBe(400);
        expect(error.data).toEqual({ detail: 'Bad request', errors: { field: 'Invalid' } });
      }
    });

    it('should use detail field for error message when available', async () => {
      const errorResponse = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };
      mockAxios.mockRejectedValue(errorResponse);

      try {
        await apiRequest('/api/test/', { method: 'POST' });
      } catch (error) {
        expect(error.message).toBe('Invalid credentials');
      }
    });

    it('should use message field for error message when detail not available', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { message: 'Internal server error' },
        },
      };
      mockAxios.mockRejectedValue(errorResponse);

      try {
        await apiRequest('/api/test/');
      } catch (error) {
        expect(error.message).toBe('Internal server error');
      }
    });

    it('should stringify error data when no message/detail available', async () => {
      const errorResponse = {
        response: {
          status: 422,
          data: { field1: 'error1', field2: 'error2' },
        },
      };
      mockAxios.mockRejectedValue(errorResponse);

      try {
        await apiRequest('/api/test/', { method: 'POST' });
      } catch (error) {
        expect(error.message).toContain('field1');
        expect(error.message).toContain('error1');
      }
    });

    it('should throw generic error on network error (no response)', async () => {
      const networkError = {
        request: {},
        message: 'Network Error',
      };
      mockAxios.mockRejectedValue(networkError);

      await expect(apiRequest('/api/test/')).rejects.toThrow('Network Error: No response received');
    });

    it('should re-throw original error if neither response nor request exists', async () => {
      const setupError = new Error('Setup error');
      mockAxios.mockRejectedValue(setupError);

      await expect(apiRequest('/api/test/')).rejects.toThrow('Setup error');
    });

    it('should handle case-insensitive method names for CSRF checking', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      // Lowercase 'post' should still trigger CSRF token fetch
      await apiRequest('/api/test/', { method: 'post' });

      // CSRF check should work with case-insensitive method
      expect(mockEnsureCsrfToken).toHaveBeenCalled();
      // The axios call is made with the method from options
      expect(mockAxios).toHaveBeenCalled();
    });

    it('should set url correctly', async () => {
      mockAxios.mockResolvedValue({ data: { success: true } });

      await apiRequest('/api/users/123/');

      expect(mockAxios).toHaveBeenCalledWith(
        expect.objectContaining({
          url: '/api/users/123/',
        })
      );
    });
  });
});
