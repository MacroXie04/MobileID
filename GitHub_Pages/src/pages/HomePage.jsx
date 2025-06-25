import React, {useEffect, useState, useRef} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import defaultProfileImg from '../assets/img/default.png'
import openDoorImg from '../assets/img/open-door.png';
import ucMercedLogo from '../assets/img/ucm3.png'; // UCM logo
import mobileIdLogo from '../assets/img/mobileid_logo.png'; // MobileID logo
import '../assets/css/mobileid.css'; // Custom CSS
import {getCurrentUser, logout} from '../services/api';

const HomePage = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const apiCallInProgress = useRef(false);

    useEffect(() => {
        const fetchCurrentUser = async () => {
            // Prevent duplicate API calls
            if (apiCallInProgress.current) return;
            apiCallInProgress.current = true;

            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    navigate('/login');
                    return;
                }

                const data = await getCurrentUser(accessToken);
                setUser(data);
            } catch (error) {
                console.error("Error fetching user:", error);
                // Only redirect if it's an authentication error
                if (error.response && (error.response.status === 401 || error.response.status === 403)) {
                    localStorage.removeItem('access_token'); // Clear invalid token
                    navigate('/login');
                }
            } finally {
                setLoading(false);
                apiCallInProgress.current = false;
            }
        };

        fetchCurrentUser();
    }, [navigate]);

    const handleLogout = () => {
        // This will remove the access token from localStorage
        logout();
        console.log("User logged out");
        navigate('/login');
    };

    if (loading) {
        // Optional: a loading spinner while fetching data
        return (
            <div className="d-flex justify-content-center align-items-center" style={{height: "100vh"}}>
                <div className="spinner-border text-light" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (!user) {
        // This will be brief as the redirect should have already happened
        return null;
    }

    const profileImageUrl = user.user_profile_img
        ? `data:image/png;base64,${user.user_profile_img}`
        : defaultProfileImg;

    return (
        <div className="container">
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '20px 40px',
                position: 'relative'
            }}>
                <div style={{flex: 1}}>
                    <Link to="/">
                        <img src={ucMercedLogo} alt="UC Merced Logo" style={{height: '60px'}}/>
                    </Link>
                </div>
                <div style={{flex: 1, display: 'flex', justifyContent: 'center'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                        <img src={mobileIdLogo} alt="Fingerprint" style={{height: '60px'}}/>
                    </div>
                </div>
                <div style={{flex: 1}}></div>
            </div>

            <div style={{borderTop: '1px solid white', margin: '0 20px'}}></div>

            {/* Main Content */}
            <main>
                {/* Centered Profile Section */}
                <div className="text-center" style={{marginTop: '2em'}}>
                    <Link to="/settings" id="setting-icon">
                        <img
                            src={profileImageUrl}
                            style={{
                                width: '100px',
                                height: '100px',
                                objectFit: 'cover',
                                borderRadius: '50%',
                                boxShadow: '0 4px 12px rgba(255, 255, 255, 0.4)',
                                transition: 'transform 0.3s ease-in-out',
                            }}
                            className="img-circle"
                            alt="User profile picture"
                        />
                    </Link>

                    <h4 className="white-h4" style={{marginTop: '0.5em', color: 'white !important'}}>
                        {user.name}
                    </h4>

                    <h4 id="student-id" className="white-h4" style={{color: 'white !important'}}>
                        {user.student_id}
                    </h4>

                    {/* Pay/Check-in Button */}
                    <div id="show-info-button" style={{marginTop: '1em'}}>
                        <button type="button" className="btn btn-trans btn-trans-default">
                            <b>PAY / Check-in</b>
                        </button>
                    </div>
                </div>

                {/* Display Barcode -- Functionality to be implemented later */}
                <div id="qrcode" className="text-center">
                    <div id="qrcode-div" style={{display: 'none'}}>Barcode</div>
                    <br/>
                    <div id="qrcode-code" style={{display: 'none'}}>
                        <div className="progress" style={{width: '70%', display: 'inline-block'}}>
                            <div
                                className="progress-bar progress-bar-white"
                                role="progressbar"
                                aria-valuenow="100"
                                aria-valuemin="0"
                                aria-valuemax="100"
                                style={{width: '100%'}}
                            ></div>
                        </div>
                    </div>
                </div>

                {/* Grid Menu */}
                <div style={{margin: 'auto', maxWidth: '320px'}}>
                    <div className="grid-container">
                        {/* First Row */}
                        <Link to="/setup" className="btn-grid">
                            <i className="fa fa-credit-card fa-2x"></i>
                            <p>Add Funds</p>
                        </Link>
                        <Link to="/balance" className="btn-grid">
                            <i className="fa fa-money-bill fa-2x"></i>
                            <p>Balance</p>
                        </Link>
                        <Link to="/lost-card" className="btn-grid">
                            <i className="fa fa-id-card fa-2x"></i>
                            <p>Lost My Card</p>
                        </Link>

                        {/* Second Row */}
                        <Link to="/emergency" className="btn-grid">
                            <i className="fa fa-exclamation-triangle fa-2x"></i>
                            <p id="server_status">Emergency</p>
                        </Link>
                        <Link to="/gym" className="btn-grid">
                            <i className="fa fa-dumbbell fa-2x"></i>
                            <p>Gym</p>
                        </Link>
                        <Link to="/resources" className="btn-grid">
                            <i className="fa fa-info fa-2x"></i>
                            <p>Resources</p>
                        </Link>

                        {/* Third Row */}
                        <button onClick={handleLogout} className="btn-grid"
                                style={{border: 'none', background: 'none'}}>
                            <i className="fa fa-sign-out-alt fa-2x"></i>
                            <p>Log out</p>
                        </button>
                        {/* The grid can be filled with more items or left as is */}
                        <div className="btn-grid-placeholder"></div>
                        <div className="btn-grid-placeholder"></div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default HomePage;
