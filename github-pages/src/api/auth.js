import { baseURL } from '@/config'

export async function login(username, password) {
  const res = await fetch(`${baseURL}/authn/token/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  return res.json();
}

export async function userInfo() {
  const res = await fetch(`${baseURL}/authn/user_info/`, {
    credentials: "include"
  });
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  await fetch(`${baseURL}/authn/logout/`, {
    method: "POST",
    credentials: "include"
  });
}

// get user profile
export async function getUserProfile() {
  const res = await fetch(`${baseURL}/authn/profile/`, {
    credentials: "include"
  });
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}

// update user profile
export async function updateUserProfile(profileData) {
  const res = await fetch(`${baseURL}/authn/profile/`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData)
  });
  if (!res.ok) throw new Error('Failed to update profile');
  return res.json();
}

// register
export async function register(userData) {
  try {
    const res = await fetch(`${baseURL}/authn/register/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(JSON.stringify(errorData));
    }
    
    return res.json();
  } catch (error) {
    // if token related error, maybe because of expired cookie, try to call logout API to clear them
    if (error.message.includes('token_not_valid') || error.message.includes('Token is expired')) {
      // call logout API to clear HTTPOnly cookies
      try {
        await fetch(`${baseURL}/authn/logout/`, {
          method: "POST",
          credentials: "include"
        });
      } catch (logoutError) {
        // even if logout fails, continue to try register
        console.warn('Failed to logout:', logoutError);
      }
      
      // try register again
      const retryRes = await fetch(`${baseURL}/authn/register/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
      });
      
      if (!retryRes.ok) {
        const errorData = await retryRes.json();
        throw new Error(JSON.stringify(errorData));
      }
      
      return retryRes.json();
    }
    
    throw error;
  }
}
