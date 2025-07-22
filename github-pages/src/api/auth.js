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
