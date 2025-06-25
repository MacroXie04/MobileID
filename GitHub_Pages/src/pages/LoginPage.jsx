// src/pages/LoginPage.jsx
import React, {useState} from "react";
import {useNavigate} from "react-router-dom";
import {getCurrentUser, login} from "../services/api";

function LoginPage() {
    const [form, setForm] = useState({username: "", password: ""});
    const [showPw, setShowPw] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [nonFieldError, setNonFieldError] = useState("");
    const navigate = useNavigate();

    // --- helpers --------------------------------------------------------------
    const hasError = (field) => (fieldErrors[field] ? "is-invalid" : "");
    const handleChange = (e) =>
        setForm((f) => ({...f, [e.target.name]: e.target.value}));

    // --- submit ---------------------------------------------------------------
    const handleSubmit = async (e) => {
        e.preventDefault();
        setFieldErrors({});
        setNonFieldError("");

        try {
            const {access} = await login(form.username, form.password);
            localStorage.setItem("access_token", access);
            navigate("/");
        } catch (err) {
            if (err.response?.status === 401) {
                setNonFieldError("Invalid username or password.");
            } else if (err.response?.data) {
                // DRF field errors (rare on login, but handle anyway)
                setFieldErrors(err.response.data);
            } else {
                setNonFieldError("Login failed. Server unreachable?");
            }
        }
    };

    // --- render ---------------------------------------------------------------
    return (
        <div
            className="container mt-5 d-flex justify-content-center align-items-center"
            style={{minHeight: "80vh"}}
        >
            <div className="card p-4 shadow-sm" style={{maxWidth: 600, width: "100%"}}>
                {/* title */}
                <h4 className="fw-bold text-center mb-1">Sign In</h4>
                <p className="text-muted text-center mb-4">login to continue</p>

                {/* server / non-field error */}
                {nonFieldError && <div className="alert alert-danger">{nonFieldError}</div>}

                <form onSubmit={handleSubmit} noValidate>
                    {/* username */}
                    <div className="mb-3">
                        <label className="form-label fw-semibold">Username *</label>
                        <input
                            className={`form-control ${hasError("username")}`}
                            name="username"
                            value={form.username}
                            onChange={handleChange}
                            required
                        />
                        {fieldErrors.username && (
                            <div className="invalid-feedback d-block">{fieldErrors.username}</div>
                        )}
                    </div>

                    {/* password */}
                    <div className="mb-3">
                        <label className="form-label fw-semibold">Password *</label>
                        <input
                            type={showPw ? "text" : "password"}
                            className={`form-control ${hasError("password")}`}
                            name="password"
                            value={form.password}
                            onChange={handleChange}
                            required
                        />
                        {fieldErrors.password && (
                            <div className="invalid-feedback d-block">{fieldErrors.password}</div>
                        )}
                    </div>

                    {/* show-password toggle */}
                    <div className="form-check mb-3">
                        <input
                            id="showPw"
                            className="form-check-input"
                            type="checkbox"
                            checked={showPw}
                            onChange={(e) => setShowPw(e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="showPw">
                            Show Password
                        </label>
                    </div>

                    {/* auxiliary links */}
                    <div className="d-flex justify-content-between align-items-center mb-4">
                        <a href="/forgot-password" className="link-secondary">
                            Forgot Password
                        </a>
                        <span className="small">
              New user? <a href="/register">Register Account</a>
            </span>
                    </div>

                    <button type="submit" className="btn btn-primary w-100">
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;
