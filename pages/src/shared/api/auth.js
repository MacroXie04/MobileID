import { ApiError, apiRequest } from './client';
import { clearAuthCookies, clearAuthStorage } from '@shared/utils/cookie';
import { clearUserInfo } from '@shared/state/authState';

export async function login(username, password) {
  try {
    const response = await apiRequest('/authn/login/', {
      method: 'POST',
      body: { username, password },
    });

    // Server sets auth cookies; no localStorage storage needed
    return response;
  } catch (error) {
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

export async function establishAuthenticatedSession() {
  const user = await userInfo();
  if (user) {
    return user;
  }

  const { refreshToken } = await import('@shared/utils/tokenRefresh');
  const refreshed = await refreshToken();
  if (!refreshed) {
    return null;
  }

  return await userInfo();
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
