const {
    startRegistration,
    startAuthentication,
    platformAuthenticatorIsAvailable,
} = SimpleWebAuthnBrowser;

function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
}

/* ---------- register ---------- */
window.registerPasskey = async () => {
    if (!(await platformAuthenticatorIsAvailable())) {
        return;
    }
    try {
        const opts = await fetch("/webauthn/passkey/reg/options").then(r => r.json());
        const regResp = await startRegistration(opts);
        const res = await fetch("/webauthn/passkey/reg/complete", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()},
            body: JSON.stringify(regResp),
        }).then(r => r.json());

        alert(res.status === "ok" ? "Registered successfully！" : "Register failed：" + JSON.stringify(res));
    } catch (e) {
        console.error(e);
        alert(e.message || "Register failed");
    }
};

/* ---------- 登录 ---------- */
window.loginWithPasskey = async () => {
  try {
    const opts = await fetch("/webauthn/passkey/auth/options").then(r => r.json());
    const authResp = await startAuthentication(opts);
    const res = await fetch("/webauthn/passkey/auth/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(authResp),
    }).then(r => r.json());

    if (res.status === "ok") window.location.replace("/");
    else alert("Login failed：" + JSON.stringify(res));
  } catch (e) {
    console.error(e);
    alert(e.message || "Login failed");
  }
};
