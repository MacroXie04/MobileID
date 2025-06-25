import React from 'react';
import {BrowserRouter, Navigate, Route, Routes} from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

function App() {
    const isLoggedIn = !!localStorage.getItem('access_token');

    // Check if we're running in development or production
    const isDevelopment = window.location.hostname === 'localhost' || 
                         window.location.hostname === '127.0.0.1';

    // Use basename only in production (GitHub Pages deployment)
    const basename = isDevelopment ? '/' : '/UCMerced-Barcode';

    return (
        <BrowserRouter basename={basename}>
            <Routes>
                <Route path="/login" element={<LoginPage/>}/>
                <Route path="/register" element={<RegisterPage/>}/>
                <Route path="/" element={isLoggedIn ? <HomePage/> : <Navigate to="/login"/>}/>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
