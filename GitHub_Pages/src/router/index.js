import {createRouter, createWebHistory} from 'vue-router'


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
                    const response = await fetch('http://127.0.0.1:8000/me/', {
                        headers: {
                            'Authorization': `Bearer ${loggedIn}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.status === 401) {
                        // Token is invalid, redirect to login
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        next({name: 'login'});
                        return;
                    }
                    
                    if (response.ok) {
                        const userData = await response.json();
                        // Check if user is active (assuming the API returns user status)
                        if (userData.is_active === false) {
                            next({name: 'account-disabled'});
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error checking user status:', error);
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
