import axios from 'axios';

// Create an Axios instance with the base URL for the API
const API = axios.create({
    baseURL: 'http://localhost:8000/',
});


// User authentication functions
export const login = async (username, password) => {
    const res = await API.post('token/', {username, password});
    return res.data;
};


export const register = async (formData) => {
    const res = await API.post('register/', formData);
    return res.data;
};


export const logout = () => {
    localStorage.removeItem('access_token');
};

// Function to get the current user information
export const getCurrentUser = async (accessToken) => {
    const res = await API.get('current_user/', {
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    });
    return res.data;
};
