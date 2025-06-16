// src/pages/LoginPage.jsx
import React, {useState} from 'react';
import {getCurrentUser, login} from '../services/api';
import {useNavigate} from 'react-router-dom';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});
    const [nonFieldError, setNonFieldError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setFieldErrors({});
        setNonFieldError('');

        try {
            const {access} = await login(username, password);
            localStorage.setItem('access_token', access);
            navigate('/');
            // Fetch user data in the background
            getCurrentUser(access).catch(error => {
                console.error('Error fetching user data:', error);
            });
        } catch (err) {
            if (err.response?.status === 401) {
                setNonFieldError('Invalid username or password.');
            } else {
                setNonFieldError('Login failed.');
            }
        }
    };

    return (
        <div className="container mt-5 d-flex justify-content-center align-items-center" style={{minHeight: '80vh'}}>
            <div className="card p-4 shadow-sm" style={{maxWidth: '500px', width: '100%'}}>
                <h3 className="text-center mb-4">Login</h3>
                <form onSubmit={handleLogin} noValidate>
                    <div className="mb-3">
                        <label className="form-label">Username</label>
                        <input
                            className="form-control"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                        {fieldErrors.username && (
                            <div className="invalid-feedback d-block">{fieldErrors.username}</div>
                        )}
                    </div>

                    <div className="mb-3">
                        <label className="form-label">Password</label>
                        <input
                            className="form-control"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        {fieldErrors.password && (
                            <div className="invalid-feedback d-block">{fieldErrors.password}</div>
                        )}
                    </div>

                    {nonFieldError && (
                        <div className="invalid-feedback d-block mb-3">{nonFieldError}</div>
                    )}

                    <button type="submit" className="btn btn-primary w-100 py-2">Login</button>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;
