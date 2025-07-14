import axios from 'axios';
import router from './router/index.js';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/',
    headers: {
        'Content-Type': 'application/json',
    }
});

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle account disabled errors
apiClient.interceptors.response.use(
    (response) => {
        // Check if response contains account status
        if (response.data && response.data.account_status) {
            const accountStatus = response.data.account_status;
            
            // Store updated user status
            localStorage.setItem('user_status', JSON.stringify(accountStatus));
            
            // Check if account is disabled or locked
            if (accountStatus.status === 'disabled' || 
                (accountStatus.status === 'locked' && !accountStatus.lock_expired)) {
                
                console.log('API response indicates disabled/locked account, redirecting to account-disabled');
                
                // Only redirect if not already on account-disabled page
                if (router.currentRoute.value.name !== 'account-disabled') {
                    router.push('/account-disabled');
                }
            }
        }
        
        return response;
    },
    (error) => {
        console.error('API Error:', error);
        
        if (error.response) {
            const status = error.response.status;
            const errorData = error.response.data || {};
            
            // Handle 401 errors that might indicate disabled accounts
            if (status === 401) {
                // Check if error specifically indicates account is disabled
                if (errorData.account_disabled || 
                    (errorData.detail && errorData.detail.includes('disabled'))) {
                    
                    console.log('401 error indicates disabled account, redirecting to account-disabled');
                    
                    // Store error-based status
                    localStorage.setItem('user_status', JSON.stringify({
                        status: 'disabled',
                        message: errorData.detail || 'Account is disabled',
                        account_disabled: true
                    }));
                    
                    // Redirect to account-disabled page if not already there
                    if (router.currentRoute.value.name !== 'account-disabled') {
                        router.push('/account-disabled');
                    }
                    
                    return Promise.reject(error);
                }
                
                // Handle other 401 errors (invalid token)
                console.log('401 error indicates invalid token, clearing user data');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_status');
                localStorage.removeItem('user_profile');
                
                // Redirect to login if not already there and not on public pages
                const publicPages = ['login', 'register', 'account-disabled'];
                if (!publicPages.includes(router.currentRoute.value.name)) {
                    router.push('/login');
                }
            }
        }
        
        return Promise.reject(error);
    }
);

export default apiClient;
