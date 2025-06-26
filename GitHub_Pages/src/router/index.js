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
      path: '/manage_barcodes',
      name: 'manage_barcodes',
      component: () => import('../views/ManageBarcodesView.vue'),
      meta: {requiresAuth: true}
    }

  ]
})

router.beforeEach((to, from, next) => {
  const loggedIn = localStorage.getItem('access_token');

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!loggedIn) {

      next({name: 'login'});
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router
