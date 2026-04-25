import { getCookie } from '@shared/utils/cookie';
import { baseURL } from '@shared/config/config';
import { useServerWakeup } from '@shared/composables/api/useServerWakeup';
import { ensureCsrfToken } from '@shared/api/csrf';
import { useToken } from '@auth/composables/useToken';

export interface AuthenticatedRequestOptions extends RequestInit {
  timeoutMs?: number;
  headers?: HeadersInit;
}

export interface AuthenticatedRequestError extends Error {
  status?: number;
  errors?: Record<string, unknown>;
  responseData?: unknown;
}

export function useAuthenticatedRequest() {
  const { checkAuthenticationError, refreshToken, handleTokenExpired } = useToken();
  const { triggerWakeup } = useServerWakeup();

  async function apiCallWithAutoRefresh<T = unknown>(
    url: string,
    options: AuthenticatedRequestOptions = {},
    retryCount = 0
  ): Promise<T> {
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

      const headers = {
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        'Content-Type': 'application/json',
        ...options.headers,
      };
      const fullUrl = url.startsWith('http') ? url : `${baseURL}${url}`;
      const { headers: _optHeaders, timeoutMs: _timeoutMs, ...restOptions } = options;

      const response = await fetch(fullUrl, {
        credentials: 'include',
        ...restOptions,
        headers,
        signal: controller.signal,
      });
      clearTimeout(id);

      let data: unknown = null;
      const contentType = response.headers?.get('content-type') || '';
      if (contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch {
          data = null;
        }
      }

      if (import.meta.env?.MODE !== 'production') {
        console.debug(`API ${response.status} ${fullUrl}`);
      }

      if (checkAuthenticationError(data, response)) {
        if (retryCount < maxRetries) {
          const refreshSuccess = await refreshToken();
          if (refreshSuccess) {
            return apiCallWithAutoRefresh<T>(url, options, retryCount + 1);
          }

          const tokenRecoverySuccess = await handleTokenExpired();
          if (tokenRecoverySuccess) {
            return apiCallWithAutoRefresh<T>(url, options, retryCount + 1);
          }

          throw new Error('Token refresh failed');
        }

        await handleTokenExpired();
        throw new Error('Max retries exceeded');
      }

      if ([502, 503, 504].includes(response.status)) {
        triggerWakeup();
        throw new Error('Server unavailable - wakeup triggered');
      }

      if (!response.ok) {
        const payload = data as { detail?: string; message?: string; errors?: Record<string, unknown> } | null;
        const error = new Error(
          `API call failed: ${response.status} - ${payload?.detail || payload?.message || 'Unknown error'}`
        ) as AuthenticatedRequestError;
        error.status = response.status;
        error.errors = payload?.errors;
        error.responseData = data;
        throw error;
      }

      if (import.meta.env?.MODE !== 'production') {
        console.debug(`API response for ${url}:`, data);
      }

      return data as T;
    } catch (error) {
      clearTimeout(id);

      const err = error as AuthenticatedRequestError;
      const isServerUnavailable =
        err?.name === 'AbortError' ||
        error === 'timeout' ||
        err?.message?.includes('Failed to fetch') ||
        err?.message?.includes('NetworkError') ||
        err?.message?.includes('Network request failed') ||
        err?.message?.includes('ECONNREFUSED') ||
        err?.message?.includes('ERR_CONNECTION_REFUSED');
      const isServerError = err?.status === 502 || err?.status === 503 || err?.status === 504;

      if (isServerUnavailable || isServerError) {
        triggerWakeup();
        throw new Error('Server unavailable - wakeup triggered');
      }

      if (
        typeof err?.message === 'string' &&
        (err.message.includes('Token') || err.message.includes('retries'))
      ) {
        throw err;
      }

      if (err?.status && err?.errors) {
        throw err;
      }

      if (import.meta.env?.MODE !== 'production') {
        console.error(`API request failed (${url}):`, err);
      }
      throw new Error(`Network error: ${err?.message || 'unknown_error'}`);
    }
  }

  return {
    apiCallWithAutoRefresh,
  };
}
