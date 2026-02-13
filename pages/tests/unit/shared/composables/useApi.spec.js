import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { useApi } from '@shared/composables/useApi.js';

// Mock dependencies
vi.mock('@app/config/config', () => ({
  baseURL: 'http://localhost:8000',
}));

const mockGetCookie = vi.fn();
vi.mock('@shared/utils/cookie', () => ({
  getCookie: () => mockGetCookie(),
}));

const mockCheckAuthenticationError = vi.fn();
const mockRefreshToken = vi.fn();
const mockHandleTokenExpired = vi.fn();
vi.mock('@auth/composables/useToken', () => ({
  useToken: () => ({
    checkAuthenticationError: mockCheckAuthenticationError,
    refreshToken: mockRefreshToken,
    handleTokenExpired: mockHandleTokenExpired,
  }),
}));

const mockGetAccessToken = vi.fn();
vi.mock('@shared/api/axios', () => ({
  getAccessToken: () => mockGetAccessToken(),
}));

const mockTriggerWakeup = vi.fn();
vi.mock('@shared/composables/useServerWakeup', () => ({
  useServerWakeup: () => ({
    triggerWakeup: mockTriggerWakeup,
  }),
}));

const mockEnsureCsrfToken = vi.fn();
vi.mock('@shared/api/csrf', () => ({
  ensureCsrfToken: () => mockEnsureCsrfToken(),
}));

describe('useApi composable', () => {
  let originalFetch;
  let api;

  beforeEach(() => {
    vi.clearAllMocks();
    originalFetch = global.fetch;
    global.fetch = vi.fn();

    // Default mock implementations
    mockGetCookie.mockReturnValue('csrf-token');
    mockGetAccessToken.mockReturnValue('access-token');
    mockCheckAuthenticationError.mockReturnValue(false);
    mockRefreshToken.mockResolvedValue(true);
    mockHandleTokenExpired.mockResolvedValue(false);
    mockEnsureCsrfToken.mockResolvedValue('csrf-token');

    api = useApi();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('apiCallWithAutoRefresh', () => {
    it('should prepend baseURL to relative URLs', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ success: true }),
      });

      await api.apiCallWithAutoRefresh('/test/endpoint/');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/endpoint/',
        expect.any(Object)
      );
    });

    it('should leave absolute URLs unchanged', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ success: true }),
      });

      await api.apiCallWithAutoRefresh('https://other-api.com/endpoint/');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://other-api.com/endpoint/',
        expect.any(Object)
      );
    });

    it('should add Authorization header when token exists', async () => {
      mockGetAccessToken.mockReturnValue('my-access-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer my-access-token',
          }),
        })
      );
    });

    it('should not add Authorization header when no token', async () => {
      mockGetAccessToken.mockReturnValue(null);
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/');

      const fetchCall = global.fetch.mock.calls[0][1];
      expect(fetchCall.headers.Authorization).toBeUndefined();
    });

    it('should add X-CSRFToken header for non-GET requests', async () => {
      mockGetCookie.mockReturnValue('my-csrf-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/', { method: 'POST' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRFToken': 'my-csrf-token',
          }),
        })
      );
    });

    it('should fetch CSRF token if not available in cookie for POST', async () => {
      mockGetCookie.mockReturnValue(null);
      mockEnsureCsrfToken.mockResolvedValue('fetched-csrf-token');
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/', { method: 'POST' });

      expect(mockEnsureCsrfToken).toHaveBeenCalled();
    });

    it('should not fetch CSRF token for GET requests', async () => {
      mockGetCookie.mockReturnValue(null);
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/', { method: 'GET' });

      expect(mockEnsureCsrfToken).not.toHaveBeenCalled();
    });

    it('should parse JSON responses', async () => {
      const responseData = { id: 1, name: 'Test' };
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve(responseData),
      });

      const result = await api.apiCallWithAutoRefresh('/test/');

      expect(result).toEqual(responseData);
    });

    it('should handle non-JSON responses gracefully', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'text/html' },
        json: () => Promise.reject(new Error('Not JSON')),
      });

      const result = await api.apiCallWithAutoRefresh('/test/');

      expect(result).toBeNull();
    });

    it('should retry once on authentication error', async () => {
      mockCheckAuthenticationError.mockReturnValueOnce(true).mockReturnValueOnce(false);
      mockRefreshToken.mockResolvedValue(true);

      global.fetch
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          headers: { get: () => 'application/json' },
          json: () => Promise.resolve({ code: 'token_not_valid' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          headers: { get: () => 'application/json' },
          json: () => Promise.resolve({ success: true }),
        });

      const result = await api.apiCallWithAutoRefresh('/test/');

      expect(mockRefreshToken).toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ success: true });
    });

    it('should call handleTokenExpired after failed refresh', async () => {
      mockCheckAuthenticationError.mockReturnValue(true);
      mockRefreshToken.mockResolvedValue(false);
      mockHandleTokenExpired.mockResolvedValue(false);

      global.fetch.mockResolvedValue({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ code: 'token_not_valid' }),
      });

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow('Token refresh failed');

      expect(mockHandleTokenExpired).toHaveBeenCalled();
    });

    it('should retry after successful token recovery', async () => {
      mockCheckAuthenticationError.mockReturnValueOnce(true).mockReturnValueOnce(false);
      mockRefreshToken.mockResolvedValue(false);
      mockHandleTokenExpired.mockResolvedValue(true); // Recovery succeeded

      global.fetch
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          headers: { get: () => 'application/json' },
          json: () => Promise.resolve({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          headers: { get: () => 'application/json' },
          json: () => Promise.resolve({ recovered: true }),
        });

      const result = await api.apiCallWithAutoRefresh('/test/');

      expect(result).toEqual({ recovered: true });
    });

    it('should throw after max retries exceeded', async () => {
      mockCheckAuthenticationError.mockReturnValue(true);
      mockRefreshToken.mockResolvedValue(true); // Refresh succeeds but auth still fails
      mockHandleTokenExpired.mockResolvedValue(false);

      global.fetch.mockResolvedValue({
        ok: false,
        status: 401,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ code: 'token_not_valid' }),
      });

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow();
    });

    it('should trigger wakeup on 502 errors', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 502,
        headers: { get: () => 'text/html' },
        json: () => Promise.reject(new Error('Not JSON')),
      });

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow(
        'Server unavailable - wakeup triggered'
      );

      expect(mockTriggerWakeup).toHaveBeenCalled();
    });

    it('should trigger wakeup on 503 errors', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 503,
        headers: { get: () => 'text/html' },
        json: () => Promise.reject(new Error('Not JSON')),
      });

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow();

      expect(mockTriggerWakeup).toHaveBeenCalled();
    });

    it('should trigger wakeup on 504 errors', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 504,
        headers: { get: () => 'text/html' },
        json: () => Promise.reject(new Error('Not JSON')),
      });

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow();

      expect(mockTriggerWakeup).toHaveBeenCalled();
    });

    it('should trigger wakeup on network errors', async () => {
      global.fetch.mockRejectedValue(new Error('Failed to fetch'));

      await expect(api.apiCallWithAutoRefresh('/test/')).rejects.toThrow();

      expect(mockTriggerWakeup).toHaveBeenCalled();
    });

    it('should throw with status and errors for validation errors (400)', async () => {
      const errorResponse = {
        detail: 'Validation failed',
        errors: { field: ['Invalid value'] },
      };
      global.fetch.mockResolvedValue({
        ok: false,
        status: 400,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve(errorResponse),
      });

      try {
        await api.apiCallWithAutoRefresh('/test/', { method: 'POST' });
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error.status).toBe(400);
        expect(error.errors).toEqual({ field: ['Invalid value'] });
      }
    });

    it('should set up abort controller with timeout', async () => {
      // Test that the API sets up proper abort handling
      // by verifying the signal is passed to fetch
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          signal: expect.any(AbortSignal),
        })
      );
    });

    it('should set credentials to include', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({}),
      });

      await api.apiCallWithAutoRefresh('/test/');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });
  });

  describe('barcode API methods', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ success: true }),
      });
    });

    it('apiGenerateBarcode should call POST /generate_barcode/', async () => {
      await api.apiGenerateBarcode();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/generate_barcode/',
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('apiGetActiveProfile should call GET /active_profile/', async () => {
      await api.apiGetActiveProfile();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/active_profile/',
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('apiGetBarcodeDashboard should call GET /barcode_dashboard/', async () => {
      await api.apiGetBarcodeDashboard();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('apiUpdateBarcodeSettings should call POST with body', async () => {
      const settings = { theme: 'dark' };
      await api.apiUpdateBarcodeSettings(settings);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(settings),
        })
      );
    });

    it('apiCreateBarcode should call PUT with barcode', async () => {
      await api.apiCreateBarcode('12345678');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ barcode: '12345678' }),
        })
      );
    });

    it('apiDeleteBarcode should call DELETE with barcode_id', async () => {
      await api.apiDeleteBarcode('bc-123');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({
          method: 'DELETE',
          body: JSON.stringify({ barcode_id: 'bc-123' }),
        })
      );
    });

    it('apiUpdateBarcodeShare should call PATCH with share_with_others', async () => {
      await api.apiUpdateBarcodeShare('bc-123', true);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({
            barcode_id: 'bc-123',
            share_with_others: true,
          }),
        })
      );
    });

    it('apiUpdateBarcodeDailyLimit should call PATCH with daily_usage_limit', async () => {
      await api.apiUpdateBarcodeDailyLimit('bc-123', 10);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/barcode_dashboard/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({
            barcode_id: 'bc-123',
            daily_usage_limit: 10,
          }),
        })
      );
    });

    it('apiCreateDynamicBarcodeWithProfile should call POST /dynamic_barcode/', async () => {
      const data = { profile: 'school', fields: {} };
      await api.apiCreateDynamicBarcodeWithProfile(data);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/dynamic_barcode/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        })
      );
    });

    it('apiTransferDynamicBarcode should call POST /transfer_dynamic_barcode/', async () => {
      const htmlContent = '<html>barcode</html>';
      await api.apiTransferDynamicBarcode(htmlContent);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/transfer_dynamic_barcode/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ html: htmlContent }),
        })
      );
    });
  });
});
