// src/pages/Login.jsx
import React, {useState} from 'react';
import {login} from '../services/auth';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async () => {
        try {
            const {access, refresh} = await login(username, password);
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);
            alert('Login successful!');
        } catch (err) {
            alert('Login failed');
        }
    };

    return (
        <div>
            <input placeholder="Username" onChange={e => setUsername(e.target.value)}/>
            <input placeholder="Password" type="password" onChange={e => setPassword(e.target.value)}/>
            <button onClick={handleLogin}>Login</button>
        </div>
    );
}

export default LoginPage;