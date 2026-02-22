import { getCookie } from '@shared/utils/cookie';
import { useToken } from '@auth/composables/useToken';
import { getAccessToken } from '@shared/api/axios';
import { baseURL } from '@app/config/config';
import { useServerWakeup } from '@shared/composables/useServerWakeup';
import { ensureCsrfToken } from '@shared/api/csrf';

export function useApi() {
  const { checkAuthenticationError, refreshToken, handleTokenExpired } = useToken();
  const { triggerWakeup } = useServerWakeup();

  /**
   * Make API calls with automatic token refresh on authentication errors
   */
  async function apiCallWithAutoRefresh(url, options = {}, retryCount = 0) {
    // Maximum number of retries, 1 time
    const maxRetries = 1;
    const controller = new AbortController();
    const timeoutMs = options.timeoutMs ?? 10000;
    const id = setTimeout(() => controller.abort('timeout'), timeoutMs);

    try {
      const method = (options.method || 'GET').toUpperCase();
      const needsCsrf = !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method);
      let csrfToken = getCookie('csrftoken');
      if (needsCsrf && !csrfToken) {
        csrfToken = await ensureCsrfToken();
      }

      // Get access token and add Authorization header
      const token = getAccessToken();
      const headers = {
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        'Content-Type': 'application/json',
        ...options.headers,
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Prepend baseURL if url doesn't start with http
      const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`;

      const { headers: _optHeaders, ...restOptions } = options;
      const res = await fetch(fullUrl, {
        credentials: 'include',
        ...restOptions,
        headers,
        signal: controller.signal,
      });
      clearTimeout(id);

      // Try parse JSON safely
      let data = null;
      const ct = res.headers?.get('content-type') || '';
      if (ct.includes('application/json')) {
        try {
          data = await res.json();
        } catch {
          data = null;
        }
      }

      if (import.meta.env?.MODE !== 'production') {
        // Avoid logging sensitive payloads; show status only in dev.
        console.debug(`API ${res.status} ${fullUrl}`);
      }

      // Check if it is an authentication error
      if (checkAuthenticationError(data, res)) {
        console.log(`Token expired (retry count: ${retryCount}/${maxRetries})`);

        if (retryCount < maxRetries) {
          console.log('Trying to refresh token and retry...');

          // try to refresh token
          const refreshSuccess = await refreshToken();

          if (refreshSuccess) {
            console.log('Token refreshed successfully, retrying...');
            // Recursive call, increase retry count
            return await apiCallWithAutoRefresh(url, options, retryCount + 1);
          } else {
            console.log('Token refresh failed, trying handleTokenExpired...');
            const tokenRecoverySuccess = await handleTokenExpired();
            if (tokenRecoverySuccess) {
              console.log('Token recovery successful, retrying request');
              return await apiCallWithAutoRefresh(url, options, retryCount + 1);
            } else {
              throw new Error('Token refresh failed');
            }
          }
        } else {
          console.log('Maximum retries reached');
          await handleTokenExpired();
          throw new Error('Max retries exceeded');
        }
      }

      // Check for server unavailable errors (502, 503, 504)
      if (res.status === 502 || res.status === 503 || res.status === 504) {
        console.log(
          'Server error detected (status: ' + res.status + '), triggering wakeup overlay'
        );
        triggerWakeup();
        throw new Error('Server unavailable - wakeup triggered');
      }

      if (!res.ok) {
        // Create error with full response data for better error handling
        const error = new Error(
          `API call failed: ${res.status} - ${data?.detail || data?.message || 'Unknown error'}`
        );
        error.status = res.status;
        error.errors = data?.errors;
        error.responseData = data;
        throw error;
      }

      // Log response in development for debugging
      if (import.meta.env?.MODE !== 'production') {
        console.debug(`API response for ${url}:`, data);
      }

      return data;
    } catch (error) {
      clearTimeout(id);

      // Detect server unavailable errors
      const isServerUnavailable =
        error?.name === 'AbortError' ||
        error === 'timeout' ||
        error?.message?.includes('Failed to fetch') ||
        error?.message?.includes('NetworkError') ||
        error?.message?.includes('Network request failed') ||
        error?.message?.includes('ECONNREFUSED') ||
        error?.message?.includes('ERR_CONNECTION_REFUSED');

      // HTTP 502/503/504 errors indicate server is unavailable
      const isServerError = error?.status === 502 || error?.status === 503 || error?.status === 504;

      if (isServerUnavailable || isServerError) {
        console.log('Server unavailable detected, triggering wakeup overlay');
        triggerWakeup();
        throw new Error('Server unavailable - wakeup triggered');
      }

      if (error?.name === 'AbortError' || error === 'timeout') {
        throw new Error('Network error: request_timeout');
      }
      if (
        typeof error?.message === 'string' &&
        (error.message.includes('Token') || error.message.includes('retries'))
      ) {
        throw error; // re-throw authentication related errors
      }
      // Re-throw API errors with status/errors intact (e.g., 400 validation errors)
      if (error?.status && error?.errors) {
        throw error;
      }
      if (import.meta.env?.MODE !== 'production') {
        console.error(`API request failed (${url}):`, error);
      }
      throw new Error(`Network error: ${error?.message || 'unknown_error'}`);
    }
  }

  /**
   * Generate barcode API call
   */
  async function apiGenerateBarcode() {
    return await apiCallWithAutoRefresh(`${baseURL}/generate_barcode/`, {
      method: 'POST',
    });
  }

  /**
   * Get active profile info based on user settings
   */
  async function apiGetActiveProfile() {
    return await apiCallWithAutoRefresh(`${baseURL}/active_profile/`, {
      method: 'GET',
    });
  }

  /**
   * Barcode Dashboard API calls
   */
  async function apiGetBarcodeDashboard() {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'GET',
    });
  }

  async function apiUpdateBarcodeSettings(settings) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async function apiCreateBarcode(barcode) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'PUT',
      body: JSON.stringify({ barcode }),
    });
  }

  async function apiDeleteBarcode(barcodeId) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'DELETE',
      body: JSON.stringify({ barcode_id: barcodeId }),
    });
  }

  async function apiUpdateBarcodeShare(barcodeId, share) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'PATCH',
      body: JSON.stringify({
        barcode_id: barcodeId,
        share_with_others: !!share,
      }),
    });
  }

  async function apiUpdateBarcodeDailyLimit(barcodeId, dailyLimit) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: 'PATCH',
      body: JSON.stringify({
        barcode_id: barcodeId,
        daily_usage_limit: dailyLimit,
      }),
    });
  }

  /**
   * Create dynamic barcode with profile information
   */
  async function apiCreateDynamicBarcodeWithProfile(data) {
    return await apiCallWithAutoRefresh(`${baseURL}/dynamic_barcode/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Transfer dynamic barcode from HTML content
   */
  async function apiTransferDynamicBarcode(htmlContent) {
    return await apiCallWithAutoRefresh(`${baseURL}/transfer_dynamic_barcode/`, {
      method: 'POST',
      body: JSON.stringify({ html: htmlContent }),
    });
  }

  return {
    apiCallWithAutoRefresh,
    apiGenerateBarcode,
    apiGetActiveProfile,
    apiGetBarcodeDashboard,
    apiUpdateBarcodeSettings,
    apiCreateBarcode,
    apiDeleteBarcode,
    apiUpdateBarcodeShare,
    apiUpdateBarcodeDailyLimit,
    apiCreateDynamicBarcodeWithProfile,
    apiTransferDynamicBarcode,
  };
}
