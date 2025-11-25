import { ApiError, apiRequest } from './client';
import { clearPublicKeyCache, encryptPassword } from '@auth/utils/encryption';
import { setAuthTokens, clearAuthTokens } from './axios';

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

    // Save tokens to localStorage if present in response
    if (response.access && response.refresh) {
      setAuthTokens({ access: response.access, refresh: response.refresh });
    }

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
    // The original implementation returned null on failure. Replicating this behavior.
    if (error instanceof ApiError) {
      console.error('Failed to fetch user info:', error.data);
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
    // Always clear tokens from localStorage on logout
    clearAuthTokens();
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

    // Save tokens to localStorage if present in response
    if (response.access && response.refresh) {
      setAuthTokens({ access: response.access, refresh: response.refresh });
    }

    return response;
  } catch (error) {
    // If token-related error, try to log out to clear cookies and then retry registration.
    const errorMessage = JSON.stringify(error.data).toLowerCase();
    if (
      error instanceof ApiError &&
      (errorMessage.includes('token_not_valid') || errorMessage.includes('token is expired'))
    ) {
      await logout();
      // Retry registration. A second failure will now correctly bubble up.
      return apiRequest('/authn/register/', { method: 'POST', body: userData });
    }
    throw error;
  }
}
