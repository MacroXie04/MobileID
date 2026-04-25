import axios from 'axios';
import { baseURL } from '@shared/config/config';
import { clearAuthCookies, clearAuthStorage } from '@shared/utils/cookie';

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// Keep the shared Axios client domain-neutral. Authenticated feature requests
// use @auth/useAuthenticatedRequest for token refresh and retry behavior.
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      clearAuthCookies();
      clearAuthStorage();
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
