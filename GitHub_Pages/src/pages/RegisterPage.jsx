import React, {useState} from "react";
import {useNavigate} from "react-router-dom";
import {register} from "../services/api";

function RegisterPage() {
    const [form, setForm] = useState({
        username: "",
        password: "",
        password2: "",
        name: "",
        student_id: "",
        user_profile_img: null,
    });
    const [fieldErrors, setFieldErrors] = useState({});
    const [nonFieldError, setNonFieldError] = useState("");
    const navigate = useNavigate();

    const handleChange = (e) => {
        const {name, value, files} = e.target;
        setForm((f) => ({
            ...f,
            [name]: files ? files[0] : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFieldErrors({});
        setNonFieldError("");

        const data = new FormData();
        Object.entries(form).forEach(([k, v]) => data.append(k, v));

        try {
            await register(data);
            navigate("/login"); // auto-redirect on success
        } catch (err) {
            if (err.response?.data) {
                const d = err.response.data;
                setFieldErrors(d);
                if (typeof d === "string") setNonFieldError(d);
            } else {
                setNonFieldError("Registration failed. Server unreachable?");
            }
        }
    };

    // helper for Bootstrap validation class
    const hasError = (field) => fieldErrors[field] ? "is-invalid" : "";

    return (
        <div className="container mt-5 d-flex justify-content-center align-items-center" style={{minHeight: "80vh"}}>
            <div className="card p-4 shadow-sm" style={{maxWidth: 600, width: "100%"}}>
                <h4 className="fw-bold text-center mb-1">Create Account</h4>
                <p className="text-muted text-center mb-4">Sign up to use Mobile ID</p>

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

                    {/* passwords */}
                    <div className="row g-3">
                        <div className="col">
                            <label className="form-label fw-semibold">Password *</label>
                            <input
                                type="password"
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
                        <div className="col">
                            <label className="form-label fw-semibold">Confirm *</label>
                            <input
                                type="password"
                                className={`form-control ${hasError("password2")}`}
                                name="password2"
                                value={form.password2}
                                onChange={handleChange}
                                required
                            />
                            {fieldErrors.password2 && (
                                <div className="invalid-feedback d-block">{fieldErrors.password2}</div>
                            )}
                        </div>
                    </div>

                    <hr/>

                    {/* real name */}
                    <div className="mb-3">
                        <label className="form-label fw-semibold">Full Name *</label>
                        <input
                            className={`form-control ${hasError("name")}`}
                            name="name"
                            value={form.name}
                            onChange={handleChange}
                            required
                        />
                        {fieldErrors.name && (
                            <div className="invalid-feedback d-block">{fieldErrors.name}</div>
                        )}
                    </div>

                    {/* student ID */}
                    <div className="mb-3">
                        <label className="form-label fw-semibold">Student ID *</label>
                        <input
                            className={`form-control ${hasError("student_id")}`}
                            name="student_id"
                            value={form.student_id}
                            onChange={handleChange}
                            required
                        />
                        {fieldErrors.student_id && (
                            <div className="invalid-feedback d-block">{fieldErrors.student_id}</div>
                        )}
                    </div>

                    {/* avatar */}
                    <div className="mb-4">
                        <label className="form-label fw-semibold">Profile Image *</label>
                        <input
                            type="file"
                            accept="image/*"
                            className={`form-control ${hasError("user_profile_img")}`}
                            name="user_profile_img"
                            onChange={handleChange}
                            required
                        />
                        {fieldErrors.user_profile_img && (
                            <div className="invalid-feedback d-block">
                                {fieldErrors.user_profile_img}
                            </div>
                        )}
                    </div>

                    <button type="submit" className="btn btn-primary w-100">
                        Register
                    </button>
                </form>
            </div>
        </div>
    );
}

export default RegisterPage;
