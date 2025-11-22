import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { clearAuthCookies, clearAuthStorage } from '@/utils/auth/cookie';
import {
  checkAuthenticationError as sharedCheckAuthenticationError,
  refreshToken as sharedRefreshToken,
} from '@/utils/auth/tokenRefresh';

const isRefreshingToken = ref(false);

export function useToken() {
  const router = useRouter();

  /**
   * Check if response indicates authentication error
   */
  function checkAuthenticationError(data, response) {
    return sharedCheckAuthenticationError(data, response);
  }

  /**
   * Refresh the access token
   */
  async function refreshToken() {
    isRefreshingToken.value = true;
    try {
      return await sharedRefreshToken();
    } finally {
      isRefreshingToken.value = false;
    }
  }

  /**
   * Handle token expiration by first trying to refresh token, then redirecting if refresh fails
   */
  async function handleTokenExpired() {
    // Prevent duplicate calls and calls during refresh
    if (window.isLoggingOut || isRefreshingToken.value) return;
    window.isLoggingOut = true;

    try {
      // First attempt to refresh the token
      const refreshSuccess = await refreshToken();

      if (refreshSuccess) {
        window.isLoggingOut = false;
        return true;
      } else {
        // Continue to logout process below
      }
    } catch (_error) {
      // Continue to logout process below
    }

    // Clear authentication information
    clearAuthCookies();
    clearAuthStorage();

    // Clear user profile cache to force reload on next login
    try {
      const { clearUserProfile } = await import('@/composables/user/useUserInfo');
      clearUserProfile();
    } catch (error) {
      console.warn('Could not clear user profile cache:', error);
    }

    // Show prompt and redirect
    setTimeout(() => {
      // Use Vue Router for redirection
      try {
        router.push('/login');
      } catch (_error) {
        window.location.href = '/login';
      }

      // Reset duplicate call flag
      setTimeout(() => {
        window.isLoggingOut = false;
      }, 1000);
    }, 100);

    // Token refresh failed, user logged out
    return false;
  }

  return {
    isRefreshingToken,
    checkAuthenticationError,
    refreshToken,
    handleTokenExpired,
  };
}
