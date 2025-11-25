import { computed, ref } from 'vue';
import { userInfo } from '@shared/api/auth';
import { useApi } from '@shared/composables/useApi';
import { hasAuthTokens } from '@auth/utils/cookie';
import { useToken } from '@auth/composables/useToken';
import { baseURL } from '@/config';
import { getAccessToken } from '@shared/api/axios';

// Global state to prevent multiple instances and API calls
const globalProfile = ref(window.userInfo?.profile || { name: '', information_id: '' });
const isLoading = ref(false);
const isLoaded = ref(false);

export function useUserInfo() {
  const { apiCallWithAutoRefresh } = useApi();
  const { refreshToken, handleTokenExpired } = useToken();

  // Avatar state
  const avatarBlobUrl = ref('');

  // Avatar URL - returns blob URL or empty string
  const avatarSrc = computed(() => avatarBlobUrl.value);

  /**
   * Load user avatar
   */
  async function loadAvatar() {
    try {
      const token = getAccessToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      console.log('Loading avatar from:', `${baseURL}/authn/user_img/`);
      let response = await fetch(`${baseURL}/authn/user_img/`, {
        method: 'GET',
        headers,
      });

      console.log('Avatar response status:', response.status);

      // Handle auth errors by attempting a single refresh + retry
      if (response.status === 401 || response.status === 403) {
        const refreshed = await refreshToken();
        if (refreshed) {
          const retryToken = getAccessToken();
          const retryHeaders = retryToken ? { Authorization: `Bearer ${retryToken}` } : {};
          response = await fetch(`${baseURL}/authn/user_img/`, {
            method: 'GET',
            headers: retryHeaders,
          });
        } else {
          await handleTokenExpired();
          avatarBlobUrl.value = '';
          return;
        }
      }

      if (response.ok) {
        const blob = await response.blob();
        console.log('Avatar blob received, size:', blob.size, 'type:', blob.type);

        // Revoke previous blob URL to avoid memory leaks
        if (avatarBlobUrl.value) {
          URL.revokeObjectURL(avatarBlobUrl.value);
        }
        avatarBlobUrl.value = URL.createObjectURL(blob);
        console.log('Avatar blob URL created:', avatarBlobUrl.value);
      } else {
        console.log('Avatar not found or error, status:', response.status);
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
      console.log('Making API call to /authn/user_info/');
      return await apiCallWithAutoRefresh(`${baseURL}/authn/user_info/`, {
        method: 'GET',
      });
    } catch (error) {
      // If it is an authentication error, it has been handled in apiCallWithAutoRefresh
      if (error.message.includes('Token')) {
        console.log('Authentication error in user info call:', error.message);
        throw error;
      }
      // If it is not an authentication error, use the original userInfo function as a fallback
      console.log('Using fallback method to get user info...');
      return await userInfo();
    }
  }

  /**
   * Load user profile data with protection against multiple concurrent calls
   */
  async function loadUserProfile(forceReload = false) {
    // Check if user has authentication tokens before making API call
    if (!hasAuthTokens() && !forceReload) {
      console.log('No auth tokens found, skipping user info load');
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

    // If currently loading, wait for the existing call to complete
    if (isLoading.value) {
      console.log('User info loading in progress, waiting...');
      while (isLoading.value) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      return globalProfile.value;
    }

    isLoading.value = true;

    try {
      console.log('Loading user info from server...');
      const data = await getUserInfoWithAutoRefresh();
      if (data?.profile) {
        globalProfile.value = data.profile;
        isLoaded.value = true;
        console.log('User info loaded successfully');
        // Load avatar after user info is loaded
        await loadAvatar();
        return data.profile;
      } else {
        console.log('No user info found, may need to login');
        return null;
      }
    } catch (error) {
      console.error('Failed to get user info:', error);
      // If the user info is not found, let the router guard handle the authentication check
      if (!error.message.includes('Token')) {
        console.log('Router guard will handle authentication check');
      }
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
    console.log('User profile cache cleared');
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
