import React, { useEffect, useState } from 'react';
import { getCurrentUser } from '../services/api';
import { useNavigate } from 'react-router-dom';

function HomePage() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    navigate('/login');
                    return;
                }
                
                const userData = await getCurrentUser(accessToken);
                setUser(userData);
            } catch (error) {
                console.error('Error fetching user data:', error);
                localStorage.removeItem('access_token');
                navigate('/login');
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

    if (loading) {
        return (
            <div className="container mt-5 text-center">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="container mt-5">
            <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                    <h3>Welcome to Mobile ID</h3>
                    <button className="btn btn-outline-danger" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
                <div className="card-body">
                    {user && (
                        <div>
                            <h5>User Information</h5>
                            <p><strong>Username:</strong> {user.username}</p>
                            {user.email && <p><strong>Email:</strong> {user.email}</p>}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default HomePage;
