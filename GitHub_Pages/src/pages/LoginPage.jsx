// src/pages/LoginPage.jsx
import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {getCurrentUser, login} from '../services/api';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPw, setShowPw] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [nonFieldError, setNonFieldError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async e => {
        e.preventDefault();
        setFieldErrors({});
        setNonFieldError('');

        try {
            const {access} = await login(username, password);
            localStorage.setItem('access_token', access);
            navigate('/');

            // 可选：后台拉取用户信息
            getCurrentUser(access).catch(err =>
                console.error('Error fetching user data:', err)
            );
        } catch (err) {
            if (err.response?.status === 401) {
                setNonFieldError('Invalid username or password.');
            } else {
                setNonFieldError('Login failed. Cannot connect to the server.');
            }
        }
    };

    return (
        <div
            className="container mt-5 d-flex justify-content-center align-items-center"
            style={{minHeight: '80vh'}}
        >
            <div className="card p-4 shadow-sm" style={{maxWidth: 500, width: '100%'}}>
                {/* 标题区域 */}
                <h1 className="fw-bold text-center mb-1">Login</h1>

                {/*  */}
                {nonFieldError && (
                    <div className="alert alert-danger" role="alert">
                        {nonFieldError}
                    </div>
                )}

                <form onSubmit={handleLogin} noValidate>
                    {/* Username */}
                    <div className="mb-3">
                        <label htmlFor="username" className="form-label fw-semibold">
                            Username <span className="text-danger">*</span>
                        </label>
                        <input
                            id="username"
                            type="text"
                            className={`form-control ${fieldErrors.username ? 'is-invalid' : ''}`}
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            required
                        />
                        {fieldErrors.username && (
                            <div className="invalid-feedback d-block">
                                {fieldErrors.username}
                            </div>
                        )}
                    </div>

                    {/* 密码 */}
                    <div className="mb-3">
                        <label htmlFor="password" className="form-label fw-semibold">
                            Password <span className="text-danger">*</span>
                        </label>
                        <input
                            id="password"
                            type={showPw ? 'text' : 'password'}
                            className={`form-control ${fieldErrors.password ? 'is-invalid' : ''}`}
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            required
                        />
                        {fieldErrors.password && (
                            <div className="invalid-feedback d-block">
                                {fieldErrors.password}
                            </div>
                        )}
                    </div>

                    {/* 显示密码切换 */}
                    <div className="form-check mb-3">
                        <input
                            id="showPw"
                            className="form-check-input"
                            type="checkbox"
                            checked={showPw}
                            onChange={e => setShowPw(e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="showPw">
                            Show Password
                        </label>
                    </div>

                    {/* 辅助链接 */}
                    <div className="d-flex justify-content-between align-items-center mb-4">
                        <a href="/forgot-password" className="link-secondary">
                            Forgot Password
                        </a>
                        <span className="small">
              New user? <a href="/register">Register Account</a>
            </span>
                    </div>

                    {/* 登录按钮 */}
                    <button type="submit" className="btn btn-primary w-100">
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;