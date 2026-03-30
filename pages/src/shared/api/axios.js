import axios from 'axios';
import { baseURL } from '@app/config/config';
import { clearAuthCookies, clearAuthStorage } from '@shared/utils/cookie';

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// Handle 401 + auto-refresh
// Delegates to the shared refreshToken() from tokenRefresh.js so that all
// refresh requests (from both the Axios interceptor and useApi/fetch paths)
// are deduplicated through a single activeRefreshTokenPromise.
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // Don't retry the refresh endpoint itself
    if (originalRequest.url?.includes('/authn/token/refresh/')) {
      return Promise.reject(error);
    }

    // Check if error is 401 and request hasn't been retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Use shared refresh (deduplicates concurrent refresh attempts)
        const { refreshToken } = await import('@shared/utils/tokenRefresh');
        const success = await refreshToken();

        if (success) {
          // Browser sends updated cookie automatically on retry
          return api(originalRequest);
        }
      } catch (_refreshError) {
        // Refresh failed
      }

      // Refresh failed — clear auth state and redirect to login
      clearAuthCookies();
      clearAuthStorage();
      if (!window.location.pathname.includes('/login')) {
        try {
          const { default: router } = await import('@app/router/index.js');
          router.push('/login');
        } catch (_routerError) {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
    return Promise.reject(error);
  }
);

export default api;
