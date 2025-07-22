const BASE = "http://127.0.0.1:8000";

export async function login(username, password) {
  const res = await fetch(`${BASE}/authn/token/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  return res.json();
}

export async function userInfo() {
  const res = await fetch(`${BASE}/authn/user_info/`, {
    credentials: "include"
  });
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  await fetch(`${BASE}/authn/logout/`, {
    method: "POST",
    credentials: "include"
  });
}

// 获取用户档案信息
export async function getUserProfile() {
  const res = await fetch(`${BASE}/authn/profile/`, {
    credentials: "include"
  });
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}

// 更新用户档案信息
export async function updateUserProfile(profileData) {
  const res = await fetch(`${BASE}/authn/profile/`, {
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
  
  const res = await fetch(`${BASE}/authn/profile/avatar/`, {
    method: "POST",
    credentials: "include",
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload avatar');
  return res.json();
}
