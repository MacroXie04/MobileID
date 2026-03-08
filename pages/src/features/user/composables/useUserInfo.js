import { computed, ref } from 'vue';
import { userInfo } from '@shared/api/auth';
import { useApi } from '@shared/composables/useApi';
import { hasAuthTokens } from '@shared/utils/cookie';
import { useToken } from '@auth/composables/useToken';
import { baseURL } from '@app/config/config';

// Global state to prevent multiple instances and API calls
const globalProfile = ref(window.userInfo?.profile || { name: '', information_id: '' });
const isLoading = ref(false);
const isLoaded = ref(false);
const avatarBlobUrl = ref('');

export function useUserInfo() {
  const { apiCallWithAutoRefresh } = useApi();
  const { refreshToken, handleTokenExpired } = useToken();

  // Avatar URL - returns blob URL or empty string
  const avatarSrc = computed(() => avatarBlobUrl.value);

  /**
   * Load user avatar
   */
  async function loadAvatar() {
    try {
      let response = await fetch(`${baseURL}/authn/user_img/`, {
        method: 'GET',
        credentials: 'include',
      });

      // Handle auth errors by attempting a single refresh + retry
      if (response.status === 401 || response.status === 403) {
        const refreshed = await refreshToken();
        if (refreshed) {
          response = await fetch(`${baseURL}/authn/user_img/`, {
            method: 'GET',
            credentials: 'include',
          });
        } else {
          await handleTokenExpired();
          avatarBlobUrl.value = '';
          return;
        }
      }

      if (response.ok) {
        const blob = await response.blob();

        // Revoke previous blob URL to avoid memory leaks
        if (avatarBlobUrl.value) {
          URL.revokeObjectURL(avatarBlobUrl.value);
        }
        avatarBlobUrl.value = URL.createObjectURL(blob);
      } else {
        avatarBlobUrl.value = '';
      }
    } catch (error) {
      console.error('Failed to load avatar:', error);
      avatarBlobUrl.value = '';
    }
  }

  /**
   * Get user info with automatic token refresh
   */
  async function getUserInfoWithAutoRefresh() {
    try {
      return await apiCallWithAutoRefresh(`${baseURL}/authn/user_info/`, {
        method: 'GET',
      });
    } catch (error) {
      // If it is an authentication error, it has been handled in apiCallWithAutoRefresh
      if (error.message.includes('Token')) {
        throw error;
      }
      // If it is not an authentication error, use the original userInfo function as a fallback
      return await userInfo();
    }
  }

  /**
   * Load user profile data with protection against multiple concurrent calls
   */
  async function loadUserProfile(forceReload = false) {
    // Check if user has authentication tokens before making API call
    if (!hasAuthTokens() && !forceReload) {
      return null;
    }

    // read from window.userInfo first
    if (window.userInfo && !forceReload) {
      globalProfile.value = window.userInfo.profile;
      isLoaded.value = true;
      // Load avatar after setting profile from window
      await loadAvatar();
      return globalProfile.value;
    }

    // If currently loading, wait for the existing call to complete (max 10s)
    if (isLoading.value) {
      const MAX_WAIT_MS = 10000;
      let waited = 0;
      while (isLoading.value && waited < MAX_WAIT_MS) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        waited += 100;
      }
      return globalProfile.value;
    }

    isLoading.value = true;

    try {
      const data = await getUserInfoWithAutoRefresh();
      if (data?.profile) {
        globalProfile.value = data.profile;
        isLoaded.value = true;
        // Load avatar after user info is loaded
        await loadAvatar();
        return data.profile;
      } else {
        return null;
      }
    } catch (error) {
      console.error('Failed to get user info:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Clear cached user profile data
   */
  function clearUserProfile() {
    globalProfile.value = { name: '', information_id: '' };
    isLoaded.value = false;
    isLoading.value = false;
    // Clean up blob URL
    if (avatarBlobUrl.value) {
      URL.revokeObjectURL(avatarBlobUrl.value);
      avatarBlobUrl.value = '';
    }
  }

  return {
    profile: globalProfile,
    avatarSrc,
    isLoading,
    isLoaded,
    getUserInfoWithAutoRefresh,
    loadUserProfile,
    loadAvatar,
    clearUserProfile,
  };
}
