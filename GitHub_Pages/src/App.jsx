import React, {useState} from 'react';
import {getCurrentUser, login} from '../services/api';

function App() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [user, setUser] = useState(null);

    const handleLogin = async () => {
        try {
            const {access} = await login(username, password);
            localStorage.setItem('access_token', access);  // 保存 token
            const userInfo = await getCurrentUser(access);
            setUser(userInfo);
        } catch (error) {
            alert('Login failed');
            console.error(error);
        }
    };

    return (
        <div style={{padding: '2rem'}}>
            {user ? (
                <div>
                    <h2>Welcome, {user.username}</h2>
                </div>
            ) : (
                <>
                    <h3>Login</h3>
                    <input
                        type="text"
                        placeholder="Username"
                        onChange={(e) => setUsername(e.target.value)}
                    /><br/>
                    <input
                        type="password"
                        placeholder="Password"
                        onChange={(e) => setPassword(e.target.value)}
                    /><br/>
                    <button onClick={handleLogin}>Login</button>
                </>
            )}
        </div>
    );
}

export default App;
