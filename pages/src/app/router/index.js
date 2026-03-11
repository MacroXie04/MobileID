import { createRouter, createWebHistory } from 'vue-router';
import { userInfo } from '@shared/api/auth';
import { refreshToken } from '@shared/utils/tokenRefresh';
import { getUserInfo, setUserInfo, isUserInfoStale, setApiError } from '@shared/state/authState';

const routes = [
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
    path: '/',
    name: 'home',
    component: () => import('@home/views/HomeView.vue'),
    meta: { requiresAuth: true, feature: 'home' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@dashboard/views/MobileIDDashboardView.vue'),
    meta: { requiresAuth: true, feature: 'dashboard' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: (_to) => ({ path: '/' }),
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

    const cached = getUserInfo();

    // If already cached and fresh, check access
    if (cached && !isUserInfoStale()) {
      // Check if User type trying to access barcode dashboard
      if (to.path === '/dashboard' && cached.groups && cached.groups.includes('User')) {
        return next({ path: '/' });
      }
      return next();
    }

    const data = await userInfo();
    if (data) {
      setUserInfo(data);
      // Check if User type trying to access barcode dashboard
      if (to.path === '/dashboard' && data.groups && data.groups.includes('User')) {
        return next({ path: '/' });
      }
      return next();
    }

    // Try refresh if user info fetch failed
    const refreshSuccess = await refreshToken();
    if (refreshSuccess) {
      const retryData = await userInfo();
      if (retryData) {
        setUserInfo(retryData);
        // Check if User type trying to access barcode dashboard
        if (to.path === '/dashboard' && retryData.groups && retryData.groups.includes('User')) {
          return next({ path: '/' });
        }
        return next();
      }
    }

    return next({ path: '/login', query: { redirect: to.fullPath } });
  } catch (_err) {
    setApiError('API server is offline');
    // If navigating to a protected route but API is down, still allow to hit Home which shows an error panel.
    return next();
  }
});

export default router;
