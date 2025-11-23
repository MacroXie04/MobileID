import axios from 'axios';
import { baseURL } from '@/config';

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false, // JWT typically doesn't need cookies, but depends on backend. User example says false.
});

// Save tokens after login/register
export function setAuthTokens({ access, refresh }) {
  localStorage.setItem('access', access);
  localStorage.setItem('refresh', refresh);
}

// Get access token
export function getAccessToken() {
  return localStorage.getItem('access');
}

// Get refresh token
export function getRefreshToken() {
  return localStorage.getItem('refresh');
}

// Clear tokens
export function clearAuthTokens() {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
}

// Attach Authorization header
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 + auto-refresh
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
      const refresh = getRefreshToken();

      if (refresh && refresh.trim()) {
        try {
          // Call refresh endpoint using axios directly to avoid interceptors
          const refreshResponse = await axios.post(
            `${baseURL}/authn/token/refresh/`,
            { refresh },
            { headers: { 'Content-Type': 'application/json' } }
          );

          const data = refreshResponse.data;

          // Verify we got tokens back
          if (!data || !data.access) {
            console.error('Refresh response missing access token:', data);
            throw new Error('Refresh response missing access token');
          }

          // Update tokens (refresh token might be rotated)
          setAuthTokens({
            access: data.access,
            refresh: data.refresh || refresh,
          });

          // Update header for the original request
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          api.defaults.headers.common['Authorization'] = `Bearer ${data.access}`;

          // Retry the original request with new token
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed (400, 401, or network error)
          console.error('Token refresh failed:', refreshError.response?.data || refreshError.message);
          clearAuthTokens();
          // Only redirect if not already on login page
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available
        clearAuthTokens();
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
