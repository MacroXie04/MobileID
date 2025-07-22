const BASE = "http://127.0.0.1:8000";

export async function login(username, password) {
  const res = await fetch(`${BASE}/authn/api/token/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  return res.json();
}

export async function userInfo() {
  const res = await fetch(`${BASE}/authn/api/user_info/`, {
    credentials: "include"
  });
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  await fetch(`${BASE}/authn/api/logout/`, {
    method: "POST",
    credentials: "include"
  });
}

// 获取用户档案信息
export async function getUserProfile() {
  const res = await fetch(`${BASE}/authn/api/profile/`, {
    credentials: "include"
  });
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}

// 更新用户档案信息
export async function updateUserProfile(profileData) {
  const res = await fetch(`${BASE}/authn/api/profile/`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData)
  });
  if (!res.ok) throw new Error('Failed to update profile');
  return res.json();
}

// 上传头像文件
export async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  const res = await fetch(`${BASE}/authn/api/profile/avatar/`, {
    method: "POST",
    credentials: "include",
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload avatar');
  return res.json();
}

// 用户注册
export async function register(userData) {
  try {
    const res = await fetch(`${BASE}/authn/api/register/`, {
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
    // 如果是token相关错误，可能是因为有过期的cookie，尝试调用logout API清除它们
    if (error.message.includes('token_not_valid') || error.message.includes('Token is expired')) {
      // 调用logout API来清除HTTPOnly cookies
      try {
        await fetch(`${BASE}/authn/logout/`, {
          method: "POST",
          credentials: "include"
        });
      } catch (logoutError) {
        // 即使logout失败也继续尝试注册
        console.warn('Failed to logout:', logoutError);
      }
      
      // 重新尝试注册
      const retryRes = await fetch(`${BASE}/authn/register/`, {
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
