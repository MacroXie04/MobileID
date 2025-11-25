import { baseURL } from '@/config';
import { getRefreshToken, setAuthTokens } from '@shared/api/axios';

let activeRefreshTokenPromise = null;
const REFRESH_WAIT_TIMEOUT_MS = 10000; // Avoid hanging forever

/**
 * Helper to wait for a promise with timeout
 */
function waitForPromiseWithTimeout(promise, timeoutMs) {
  let timeoutId;
  return new Promise((resolve, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error('refresh_timeout'));
    }, timeoutMs);

    promise
      .then((value) => resolve(value))
      .catch((error) => reject(error))
      .finally(() => clearTimeout(timeoutId));
  });
}

/**
 * Check if response indicates authentication error
 */
export function checkAuthenticationError(data, response) {
  const isTokenInvalid =
    data?.code === 'token_not_valid' ||
    data?.detail?.includes('token not valid') ||
    data?.detail?.includes('Token is expired') ||
    data?.detail?.includes('Invalid token') ||
    response?.status === 401 ||
    response?.status === 403;

  return !!isTokenInvalid;
}

/**
 * Shared token refresh logic
 * Returns a promise that resolves to true (success) or false (failure)
 */
export function refreshToken() {
  const refreshTokenValue = getRefreshToken();
  if (!refreshTokenValue) {
    return Promise.resolve(false);
  }

  // If a refresh is already in progress, return the existing promise (with timeout wrapper)
  if (activeRefreshTokenPromise) {
    return waitForPromiseWithTimeout(activeRefreshTokenPromise, REFRESH_WAIT_TIMEOUT_MS).catch(
      () => false
    );
  }

  // Start a new token refresh
  activeRefreshTokenPromise = (async () => {
    try {
      const res = await fetch(`${baseURL}/authn/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshTokenValue }),
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

      if (res.ok && data?.access) {
        setAuthTokens({
          access: data.access,
          refresh: data.refresh || refreshTokenValue,
        });
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
