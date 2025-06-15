import axios from 'axios';

const API = axios.create({
    baseURL: 'http://localhost:8000/',
});

export const login = async (username, password) => {
    const res = await API.post('token/', {username, password});
    return res.data;
};

export const getCurrentUser = async (accessToken) => {
    const res = await API.get('me/', {
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    });
    return res.data;
};