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
            meta: {requiresAuth: true}
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

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!loggedIn) {
            next({name: 'login'});
        } else {
            // Check if user is disabled (only for non-account-disabled routes)
            if (to.name !== 'account-disabled') {
                try {
                    // Check user status by making a request to the API
                    const response = await apiClient.get('/api/me/');
                    
                    if (response.status === 401) {
                        // Token is invalid, redirect to login
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        next({name: 'login'});
                        return;
                    }
                    
                    if (response.status === 200) {
                        const userData = response.data;
                        
                        // Check the new comprehensive account status
                        if (userData.account_status) {
                            const accountStatus = userData.account_status;
                            
                            // Handle different account statuses
                            switch (accountStatus.status) {
                                case 'disabled':
                                    // User account is disabled
                                    console.log('User account is disabled:', accountStatus.message);
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
                    
                    // If there's a network error or API is unavailable, 
                    // check if we have cached user status
                    const cachedStatus = localStorage.getItem('user_status');
                    if (cachedStatus) {
                        try {
                            const status = JSON.parse(cachedStatus);
                            if (status.status === 'disabled' || status.status === 'locked') {
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
            next();
        }
    } else {
        next();
    }
});

export default router
