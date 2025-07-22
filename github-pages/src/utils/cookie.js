/**
 * Cookie utility functions
 */

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @returns {string} Cookie value or empty string if not found
 */
export function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

/**
 * Clear authentication-related cookies
 */
export function clearAuthCookies() {
  const authCookies = ['csrftoken', 'sessionid', 'access_token', 'refresh_token'];
  authCookies.forEach(cookieName => {
    document.cookie = `${cookieName}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;`;
    document.cookie = `${cookieName}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=${window.location.hostname};`;
  });
}

/**
 * Clear authentication-related storage items
 */
export function clearAuthStorage() {
  const authKeys = ['access_token', 'refresh_token', 'user_info', 'auth_token'];
  authKeys.forEach(key => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
}

/**
 * Check if user appears to be authenticated based on cookies/storage
 * @returns {boolean} True if authentication tokens are present
 */
export function hasAuthTokens() {
  const csrfToken = getCookie('csrftoken');
  const sessionId = getCookie('sessionid');
  const accessToken = getCookie('access_token') || localStorage.getItem('access_token');
  
  return !!(csrfToken && (sessionId || accessToken));
} 