import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';
import {
  getUserInfo,
  isUserInfoStale,
  refreshToken,
  setApiError,
  setUserInfo,
  userInfo,
} from '@auth';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'auth-login',
    component: () => import('@auth/views/login/LoginView.vue'),
    meta: { feature: 'auth' },
  },
  {
    path: '/register',
    name: 'auth-register',
    component: () => import('@auth/views/register/RegisterView.vue'),
    meta: { feature: 'auth' },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: () => import('@auth/views/privacy/PrivacyView.vue'),
    meta: { feature: 'auth' },
  },
  {
    path: '/privacy.html',
    redirect: '/privacy',
  },
  {
    path: '/pending',
    name: 'pending-activation',
    component: () => import('@auth/views/pending/PendingActivationView.vue'),
    meta: { requiresAuth: true, feature: 'auth' },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@home/views/HomeView.vue'),
    meta: { requiresAuth: true, requiresActivation: true, feature: 'home' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@dashboard/views/MobileIDDashboardView.vue'),
    meta: { requiresAuth: true, requiresActivation: true, feature: 'dashboard' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: () => ({ path: '/' }),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Global auth guard: checks meta.requiresAuth and caches user info in a single place
router.beforeEach(async (to, _from, next) => {
  try {
    if (!to.meta.requiresAuth) return next();

    let data = getUserInfo();

    if (!data || isUserInfoStale()) {
      data = await userInfo();
      if (!data) {
        // Try refresh if user info fetch failed
        const refreshSuccess = await refreshToken();
        if (refreshSuccess) {
          data = await userInfo();
        }
      }
      if (data) {
        setUserInfo(data);
      }
    }

    if (!data) {
      return next({ path: '/login', query: { redirect: to.fullPath } });
    }

    // Redirect non-activated users to pending page for activation-required routes
    if (to.meta.requiresActivation && !data.is_activated) {
      return next({ name: 'pending-activation' });
    }

    // Redirect activated users away from the pending page
    if (to.name === 'pending-activation' && data.is_activated) {
      return next({ path: '/' });
    }

    return next();
  } catch (_err) {
    setApiError('API server is offline');
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }
});

export default router;
