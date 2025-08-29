import { apiRequest, ApiError } from './client';

export async function login(username, password) {
    // NOTE: This is a change from the original behavior.
    // The original `login` function did not throw an error on a non-2xx response
    // (e.g., for invalid credentials). This new version WILL throw an `ApiError`.
    // The `handleSubmit` function in `Login.vue` should be updated to catch this
    // error and display the message from `error.data` or `error.message`.
    // This creates a more consistent and robust error handling pattern.
    return apiRequest('/authn/token/', {
        method: 'POST',
        body: { username, password },
    });
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

// Passkeys APIs
export async function passkeyRegisterOptions() {
    return apiRequest('/authn/passkeys/register/options/');
}

export async function passkeyRegisterVerify(credential) {
    return apiRequest('/authn/passkeys/register/verify/', {
        method: 'POST',
        body: credential,
    });
}

export async function passkeyAuthOptions(username) {
    return apiRequest('/authn/passkeys/auth/options/', {
        method: 'POST',
        body: { username },
    });
}

export async function passkeyAuthVerify(credential) {
    return apiRequest('/authn/passkeys/auth/verify/', {
        method: 'POST',
        body: credential,
    });
}

// register
export async function register(userData) {
    try {
        return await apiRequest('/authn/register/', {
            method: 'POST',
            body: userData,
        });
    } catch (error) {
        // If token-related error, try to log out to clear cookies and then retry registration.
        const errorMessage = JSON.stringify(error.data).toLowerCase();
        if (error instanceof ApiError && (errorMessage.includes('token_not_valid') || errorMessage.includes('token is expired'))) {
            await logout();
            // Retry registration. A second failure will now correctly bubble up.
            return apiRequest('/authn/register/', { method: 'POST', body: userData });
        }
        throw error;
    }
}
