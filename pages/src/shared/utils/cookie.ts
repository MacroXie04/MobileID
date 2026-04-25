/**
 * Cookie utility functions
 */

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @returns {string} Cookie value or empty string if not found
 */
export function getCookie(name: string) {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const m = document.cookie.match(new RegExp('(^| )' + escapedName + '=([^;]+)'));
  return m ? decodeURIComponent(m[2]) : '';
}

/**
 * Clear authentication-related cookies
 */
export function clearAuthCookies() {
  const authCookies = ['csrftoken', 'sessionid', 'access_token', 'refresh_token'];
  authCookies.forEach((cookieName) => {
    // Client cannot set HttpOnly, but we can clear client-visible cookies and advise security attrs.
    // path=/ ensures we clear for the whole site; domain current hostname for good measure.
    document.cookie = `${cookieName}=; Max-Age=0; Path=/; SameSite=Lax;`;
    document.cookie = `${cookieName}=; Max-Age=0; Path=/; Domain=${window.location.hostname}; SameSite=Lax;`;
  });
}

/**
 * Clear authentication-related storage items
 */
export function clearAuthStorage() {
  const authKeys = [
    'access_token',
    'refresh_token',
    'user_info',
    'auth_token',
    'access',
    'refresh',
  ];
  authKeys.forEach((key) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
}

/**
 * Check if user appears to be authenticated based on cookies/cached state.
 *
 * HttpOnly JWT cookies are invisible to JS, so we use the presence of
 * the csrftoken cookie (set alongside auth cookies) or a cached
 * userInfo as a reasonable proxy for an active session.
 *
 * @returns {boolean} True if authentication tokens are likely present
 */
export function hasAuthTokens() {
  return !!getCookie('csrftoken');
}

/**
 * Recommendation for server-side cookie flags (documentation only):
 * - Set cookies as: Secure; SameSite=Strict (or Lax for cross-origin redirects); Path=/; HttpOnly (server-only)
 * - Do not attempt to set HttpOnly from client; that must be done on the server.
 */
