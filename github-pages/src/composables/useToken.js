import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { getCookie, clearAuthCookies, clearAuthStorage } from '@/utils/cookie';
import { baseURL } from '@/config'

const isRefreshingToken = ref(false);
let activeRefreshTokenPromise = null;

export function useToken() {
  const router = useRouter();

  /**
   * Check if response indicates authentication error
   */
  function checkAuthenticationError(data, response) {
    const isTokenInvalid = 
      data?.code === "token_not_valid" ||
      data?.detail?.includes("token not valid") ||
      data?.detail?.includes("Token is expired") ||
      data?.detail?.includes("Invalid token") ||
      response?.status === 401 ||
      response?.status === 403;
      
    if (isTokenInvalid) {
      return true;
    }
    
    return false;
  }

  /**
   * Refresh the access token
   */
  async function refreshToken() {
    // If a refresh is already in progress, wait for it to complete
    if (activeRefreshTokenPromise) {
      return activeRefreshTokenPromise;
    }

    isRefreshingToken.value = true;
    
    // Start a new token refresh
    activeRefreshTokenPromise = (async () => {
      try {
        const res = await fetch(`${baseURL}/authn/token/refresh/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
          }
        });
        
        const data = await res.json();
        
        if (res.ok && data) {
          return true;
        } else {
          return false;
        }
      } catch (error) {
        return false;
      } finally {
        isRefreshingToken.value = false;
        activeRefreshTokenPromise = null;
      }
    })();
    
    return activeRefreshTokenPromise;
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
    } catch (error) {
      // Continue to logout process below
    }
    
    // Clear authentication information
    clearAuthCookies();
    clearAuthStorage();
    
    // Clear user profile cache to force reload on next login
    try {
      const { clearUserProfile } = await import('@/composables/useUserInfo');
      clearUserProfile();
    } catch (error) {
      console.warn("Could not clear user profile cache:", error);
    }
    
    // Show prompt and redirect
    setTimeout(() => {
      
      // Use Vue Router for redirection
      try {
        router.push('/login');
      } catch (error) {
        window.location.href = "/login";
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
    handleTokenExpired
  };
} 