import {createRouter, createWebHistory} from 'vue-router'
import apiClient from '../api.js'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/LoginView.vue')
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('../views/RegisterView.vue')
        },
        {
            path: '/',
            name:
                'home',
            component:
                () => import('../views/HomeView.vue'),
            meta:
                {requiresAuth: true}
        },
        {
            path: '/profile_edit',
            name: 'profile_edit',
            component: () => import('../views/ProfileEditView.vue'),
            meta: {requiresAuth: true}
        },
        {
            path: '/manage_barcode',
            name: 'manage_barcode',
            component: () => import('../views/ManageBarcodesView.vue'),
            meta: {requiresAuth: true}
        },
        {
            path: '/barcode_settings',
            name: 'barcode_settings',
            component: () => import('../views/BarcodeSettingsView.vue'),
            meta: {requiresAuth: true}
        },
        {
            path: '/account-disabled',
            name: 'account-disabled',
            component: () => import('../views/AccountDisabledView.vue'),
            meta: {requiresAuth: false}
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'not-found',
            component: () => import('../views/NotFoundView.vue')
        }

    ]
})

router.beforeEach(async (to, from, next) => {
    const loggedIn = localStorage.getItem('access_token');
    
    console.log('Route guard - navigating to:', to.name, 'from:', from.name);
    console.log('Has access token:', !!loggedIn);

    // Pages that don't require authentication and shouldn't trigger status checks
    const publicPages = ['login', 'register'];
    const isPublicPage = publicPages.includes(to.name);
    
    // If user is not logged in
    if (!loggedIn) {
        // If trying to access a protected route, redirect to login
        if (to.matched.some(record => record.meta.requiresAuth)) {
            next({name: 'login'});
        } else {
            next();
        }
        return;
    }

    // User is logged in - check status for all pages except public pages and account-disabled
    if (!isPublicPage && to.name !== 'account-disabled') {
        console.log('Checking user status for route:', to.name);
        try {
            // Check user status by making a request to the API
            const response = await apiClient.get('/api/me/');
            
            if (response.status === 401) {
                console.log('API returned 401 - token invalid');
                // Token is invalid, redirect to login
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_status');
                localStorage.removeItem('user_profile');
                next({name: 'login'});
                return;
            }
            
            if (response.status === 200) {
                const userData = response.data;
                console.log('User data received:', userData);
                
                // Check the new comprehensive account status
                if (userData.account_status) {
                    const accountStatus = userData.account_status;
                    
                    // Handle different account statuses
                    switch (accountStatus.status) {
                        case 'disabled':
                            // User account is disabled
                            console.log('User account is disabled:', accountStatus.message);
                            console.log('Redirecting to account-disabled page');
                            // Store status before redirecting
                            localStorage.setItem('user_status', JSON.stringify(accountStatus));
                            next({name: 'account-disabled'});
                            return;
                            
                        case 'locked':
                            // User account is locked
                            console.log('User account is locked:', accountStatus.message);
                            if (accountStatus.locked_until) {
                                const lockTime = new Date(accountStatus.locked_until);
                                const now = new Date();
                                if (lockTime > now) {
                                    // Account is still locked, redirect to disabled page
                                    localStorage.setItem('user_status', JSON.stringify(accountStatus));
                                    next({name: 'account-disabled'});
                                    return;
                                }
                            }
                            break;
                            
                        case 'lock_expired':
                            // Lock has expired, user can proceed
                            console.log('Account lock has expired, user can proceed');
                            break;
                            
                        case 'active':
                            // User account is active and unlocked
                            console.log('User account is active');
                            break;
                            
                        case 'no_profile':
                            // User exists but no profile, allow access
                            console.log('User has no profile, allowing access');
                            break;
                            
                        default:
                            // Unknown status, log and allow access
                            console.warn('Unknown account status:', accountStatus.status);
                            break;
                    }
                } else {
                    // Fallback to old is_active check for backward compatibility
                    if (userData.is_active === false) {
                        console.log('User account is inactive (legacy check)');
                        // Store minimal status info
                        localStorage.setItem('user_status', JSON.stringify({ 
                            status: 'disabled', 
                            message: 'Account is inactive',
                            is_active: false 
                        }));
                        next({name: 'account-disabled'});
                        return;
                    }
                }
                
                // Store user status in localStorage for components to access
                localStorage.setItem('user_status', JSON.stringify(userData.account_status || { status: 'unknown' }));
                localStorage.setItem('user_profile', JSON.stringify(userData.userprofile || {}));
                
            } else {
                console.error('Unexpected response status:', response.status);
                // If we can't determine user status, allow access to prevent blocking
            }
        } catch (error) {
            console.error('Error checking user status:', error);
            console.log('Error response:', error.response?.data);
            console.log('Error status:', error.response?.status);
            
            // Check if this is an account disabled error from the API
            if (error.response?.status === 401) {
                const errorData = error.response.data || {};
                
                // If the error indicates account is disabled, redirect to disabled page
                if (errorData.account_disabled || 
                    (errorData.detail && errorData.detail.includes('disabled'))) {
                    console.log('401 error indicates disabled account, redirecting to account-disabled');
                    // Store status from error response
                    localStorage.setItem('user_status', JSON.stringify({ 
                        status: 'disabled', 
                        message: errorData.detail || 'Account is disabled',
                        account_disabled: true 
                    }));
                    next({name: 'account-disabled'});
                    return;
                }
                
                // Otherwise, it's likely an invalid token
                console.log('401 error indicates invalid token, redirecting to login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_status');
                localStorage.removeItem('user_profile');
                next({name: 'login'});
                return;
            }
            
            // If there's a network error or API is unavailable, 
            // check if we have cached user status
            const cachedStatus = localStorage.getItem('user_status');
            if (cachedStatus) {
                try {
                    const status = JSON.parse(cachedStatus);
                    console.log('Using cached user status:', status);
                    if (status.status === 'disabled' || status.status === 'locked') {
                        console.log('Cached status indicates disabled/locked account, redirecting');
                        next({name: 'account-disabled'});
                        return;
                    }
                } catch (parseError) {
                    console.error('Error parsing cached user status:', parseError);
                }
            }
            
            // If there's an error checking user status, allow the request to proceed
            // This prevents blocking users due to network issues
        }
    }

    // For protected routes, ensure user is authenticated
    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!loggedIn) {
            next({name: 'login'});
            return;
        }
    }

    // Allow navigation
    next();
});

export default router
