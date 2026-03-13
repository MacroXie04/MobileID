import { ApiError, apiRequest } from './client';
import { clearPublicKeyCache, encryptPassword } from '@shared/utils/encryption';
import { clearAuthCookies, clearAuthStorage } from '@shared/utils/cookie';
import { clearUserInfo } from '@shared/state/authState';

export async function fetchLoginChallenge() {
  return apiRequest('/authn/login-challenge/');
}

export async function login(username, password) {
  // NOTE: This is a change from the original behavior.
  // The original `login` function did not throw an error on a non-2xx response
  // (e.g., for invalid credentials). This new version WILL throw an `ApiError`.
  // The `handleSubmit` function in `Login.vue` should be updated to catch this
  // error and display the message from `error.data` or `error.message`.
  // This creates a more consistent and robust error handling pattern.

  try {
    const challenge = await fetchLoginChallenge();
    const encryptedPassword = await encryptPassword(password, challenge);

    // Use the new encrypted-only login endpoint
    const response = await apiRequest('/authn/login/', {
      method: 'POST',
      body: { username, password: encryptedPassword },
    });

    // Server sets auth cookies; no localStorage storage needed
    return response;
  } catch (error) {
    // If we get a 401/410, the key might have rotated - clear cache
    if (error instanceof ApiError && (error.status === 401 || error.status === 410)) {
      clearPublicKeyCache();
    }

    if (error instanceof ApiError) {
      const detail = error.data?.detail || 'Invalid username or password.';
      const existingData = error.data && typeof error.data === 'object' ? error.data : {};
      throw new ApiError(detail, error.status, { ...existingData, detail });
    }
    throw error;
  }
}

export async function userInfo() {
  try {
    return await apiRequest('/authn/user_info/');
  } catch (error) {
    if (error instanceof ApiError) {
      // Return null for auth errors (401/403) to indicate "not authenticated".
      // Re-throw server errors (5xx) so callers can distinguish them.
      if (error.status >= 500) {
        throw error;
      }
      return null;
    }
    // Re-throw other errors (e.g., network errors)
    throw error;
  }
}

export async function logout() {
  try {
    // The original implementation ignored errors. We'll log a warning.
    await apiRequest('/authn/logout/', { method: 'POST' });
  } catch (error) {
    console.warn('Logout request failed:', error);
  } finally {
    // Always clear cookies, storage, and cached user info on logout
    clearAuthCookies();
    clearAuthStorage();
    clearUserInfo();
  }
}

// get user profile
export async function getUserProfile() {
  return apiRequest('/authn/profile/');
}

// update user profile
export async function updateUserProfile(profileData) {
  return apiRequest('/authn/profile/', {
    method: 'PUT',
    body: profileData,
  });
}

// register
export async function register(userData) {
  try {
    const response = await apiRequest('/authn/register/', {
      method: 'POST',
      body: userData,
    });

    // Server sets auth cookies; no localStorage storage needed
    return response;
  } catch (error) {
    // If token-related error, try to log out to clear cookies and then retry registration.
    if (error instanceof ApiError) {
      const errorMessage = JSON.stringify(error.data || {}).toLowerCase();
      if (errorMessage.includes('token_not_valid') || errorMessage.includes('token is expired')) {
        await logout();
        // Retry registration. A second failure will now correctly bubble up.
        return apiRequest('/authn/register/', { method: 'POST', body: userData });
      }
    }
    throw error;
  }
}
