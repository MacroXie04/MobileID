import { getCookie } from '@/utils/cookie';
import { useToken } from './useToken';
import { baseURL } from '@/config'

export function useApi() {
  const { checkAuthenticationError, refreshToken, handleTokenExpired } = useToken();

  /**
   * Make API calls with automatic token refresh on authentication errors
   */
  async function apiCallWithAutoRefresh(url, options = {}, retryCount = 0) {
    // Maximum number of retries, 1 time
    const maxRetries = 1;
    
    try {
      const res = await fetch(url, {
        credentials: "include",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json",
          ...options.headers
        },
        ...options
      });
      
      const data = await res.json();
      console.log(`API Response from ${url}:`, data);
      
      // Check if it is an authentication error
      if (checkAuthenticationError(data, res)) {
        console.log(`Token expired (retry count: ${retryCount}/${maxRetries})`);
        
        if (retryCount < maxRetries) {
          console.log("Trying to refresh token and retry...");
          
          // try to refresh token
          const refreshSuccess = await refreshToken();
          
          if (refreshSuccess) {
            console.log("Token refreshed successfully, retrying...");
            // Recursive call, increase retry count
            return await apiCallWithAutoRefresh(url, options, retryCount + 1);
          } else {
            console.log("Token refresh failed, trying handleTokenExpired...");
            const tokenRecoverySuccess = await handleTokenExpired();
            if (tokenRecoverySuccess) {
              console.log("Token recovery successful, retrying request");
              return await apiCallWithAutoRefresh(url, options, retryCount + 1);
            } else {
              throw new Error("Token refresh failed");
            }
          }
        } else {
          console.log("Maximum retries reached, trying final token recovery...");
          const tokenRecoverySuccess = await handleTokenExpired();
          if (tokenRecoverySuccess) {
            console.log("Final token recovery successful, retrying request");
            return await apiCallWithAutoRefresh(url, options, retryCount + 1);
          } else {
            throw new Error("Max retries exceeded");
          }
        }
      }
      
      if (!res.ok) {
        // Create error with full response data for better error handling
        const error = new Error(`API call failed: ${res.status} - ${data?.detail || data?.message || 'Unknown error'}`);
        error.status = res.status;
        error.errors = data?.errors;
        error.responseData = data;
        throw error;
      }
      return data;
      
    } catch (error) {
      if (error.message.includes("Token") || error.message.includes("retries")) {
        throw error; // re-throw authentication related errors
      }
      console.error(`API request failed (${url}):`, error);
      throw new Error(`Network error: ${error.message}`);
    }
  }

  /**
   * Generate barcode API call
   */
  async function apiGenerateBarcode() {
    return await apiCallWithAutoRefresh(`${baseURL}/generate_barcode/`, {
      method: "POST"
    });
  }

  /**
   * Barcode Dashboard API calls
   */
  async function apiGetBarcodeDashboard() {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: "GET"
    });
  }

  async function apiUpdateBarcodeSettings(settings) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: "POST",
      body: JSON.stringify(settings)
    });
  }

  async function apiCreateBarcode(barcode) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: "PUT",
      body: JSON.stringify({ barcode })
    });
  }

  async function apiDeleteBarcode(barcodeId) {
    return await apiCallWithAutoRefresh(`${baseURL}/barcode_dashboard/`, {
      method: "DELETE", 
      body: JSON.stringify({ barcode_id: barcodeId })
    });
  }

  return {
    apiCallWithAutoRefresh,
    apiGenerateBarcode,
    apiGetBarcodeDashboard,
    apiUpdateBarcodeSettings,
    apiCreateBarcode,
    apiDeleteBarcode
  };
} 