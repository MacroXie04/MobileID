import { baseURL } from '@app/config/config';
import { invalidateUserInfoCache } from '@shared/state/authState';

let activeRefreshTokenPromise = null;

/**
 * Check if response indicates authentication error
 */
export function checkAuthenticationError(data, response) {
  const isTokenInvalid =
    data?.code === 'token_not_valid' ||
    data?.detail?.includes('token not valid') ||
    data?.detail?.includes('Token is expired') ||
    data?.detail?.includes('Invalid token') ||
    response?.status === 401;
  // NOTE: 403 intentionally excluded — it means "authenticated but
  // lacks permission", not "token invalid". Including it caused
  // unnecessary token refresh loops on permission-denied responses.

  return !!isTokenInvalid;
}

/**
 * Shared token refresh logic
 * Returns a promise that resolves to true (success) or false (failure)
 *
 * Uses HttpOnly cookies — browser sends refresh_token cookie automatically.
 */
export function refreshToken() {
  // If a refresh is already in progress, all callers share the same promise
  if (activeRefreshTokenPromise) {
    return activeRefreshTokenPromise;
  }

  // Start a new token refresh
  activeRefreshTokenPromise = (async () => {
    try {
      const res = await fetch(`${baseURL}/authn/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      // Be tolerant of empty or non-JSON responses
      let data = null;
      const contentTypeHeader = res.headers?.get('content-type') || '';
      if (contentTypeHeader.includes('application/json')) {
        try {
          data = await res.json();
        } catch (_ignored) {
          // Ignore JSON parse issues
        }
      }

      if (res.ok) {
        // Server sets new cookies in response; no localStorage needed
        // Invalidate cached userInfo so the router guard re-fetches
        invalidateUserInfoCache();
        return true;
      }

      // If server indicates authentication error, treat as refresh failure
      if (checkAuthenticationError(data, res)) {
        return false;
      }

      return false;
    } catch (_error) {
      return false;
    } finally {
      activeRefreshTokenPromise = null;
    }
  })();

  return activeRefreshTokenPromise;
}

/**
 * Check if a token refresh is currently in progress
 */
export function isRefreshing() {
  return !!activeRefreshTokenPromise;
}
