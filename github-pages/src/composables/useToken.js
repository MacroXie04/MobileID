import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { getCookie, clearAuthCookies, clearAuthStorage } from '@/utils/cookie';
import { baseURL } from '@/config'

const isRefreshingToken = ref(false);

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
      console.log("Authentication error detected:", data);
      return true;
    }
    
    return false;
  }

  /**
   * Refresh the access token
   */
  async function refreshToken() {
    // Prevent concurrent refresh
    if (isRefreshingToken.value) {
      console.log("Token refresh in progress, waiting for completion...");
      // Wait for current refresh to complete
      while (isRefreshingToken.value) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      return true; // Assume refresh success, let the caller retry
    }

    isRefreshingToken.value = true;
    
    try {
      console.log("Attempting to refresh access token...");
      
      const res = await fetch(`${baseURL}/authn/token/refresh/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json"
        }
      });
      
      const data = await res.json();
      console.log("Token refresh response:", data);
      
      if (res.ok && data) {
        console.log("Token refresh successful");
        return true;
      } else {
        console.log("Token refresh failed:", data);
        return false;
      }
    } catch (error) {
      console.error("Token refresh request failed:", error);
      return false;
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
    
    console.log("Handling token expiration, attempting token refresh first...");
    
    try {
      // First attempt to refresh the token
      const refreshSuccess = await refreshToken();
      
      if (refreshSuccess) {
        console.log("Token refresh successful, user can continue");
        window.isLoggingOut = false;
        return true; // Token refreshed successfully
      } else {
        console.log("Token refresh failed, proceeding with logout...");
        // Continue to logout process below
      }
    } catch (error) {
      console.error("Token refresh error:", error);
      // Continue to logout process below
    }
    
    // Token refresh failed, clear authentication information
    console.log("Clearing authentication information and redirecting to login...");
    
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
      alert("Login expired, please login again");
      
      // Use Vue Router for redirection
      try {
        console.log("Redirecting to login page...");
        router.push('/login');
        console.log("Redirected to login page via Vue Router");
      } catch (error) {
        console.error("Vue Router redirection failed, using native redirection:", error);
        window.location.href = "/login";
        console.log("Redirected to login page via native method");
      }
      
      // Reset duplicate call flag
      setTimeout(() => {
        window.isLoggingOut = false;
        console.log("Reset logout status flag");
      }, 1000);
    }, 100);
    
    return false; // Token refresh failed, user logged out
  }

  return {
    isRefreshingToken,
    checkAuthenticationError,
    refreshToken,
    handleTokenExpired
  };
} 