import React, {useState} from 'react';
import {getCurrentUser, login} from './services/api';

function App() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [userInfo, setUserInfo] = useState(null);

    const handleLogin = async () => {
        try {
            const {access} = await login(username, password);
            const user = await getCurrentUser(access);
            setUserInfo(user);
        } catch (error) {
            alert('Login failed');
        }
    };

    return (
        <div style={{padding: '2rem'}}>
            {userInfo ? (
                <h3>Welcome, {userInfo.username}</h3>
            ) : (
                <>
                    <h3>Login</h3>
                    <input placeholder="Username" onChange={e => setUsername(e.target.value)}/><br/>
                    <input type="password" placeholder="Password" onChange={e => setPassword(e.target.value)}/><br/>
                    <button onClick={handleLogin}>Login</button>
                </>
            )}
        </div>
    );
}

export default App;