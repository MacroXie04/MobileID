import { createRouter, createWebHistory } from "vue-router";
import { userInfo } from "@/api/auth";

const Login = () => import("@/views/Login.vue");
const Home  = () => import("@/views/Home.vue");
const ProfileEdit = () => import("@/views/ProfileEdit.vue");
const Register = () => import("@/views/Register.vue");
const BarcodeDashboard = () => import("@/views/BarcodeDashboard.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/register", component: Register },
    { path: "/",      component: Home,  meta: { requiresAuth: true } },
    { path: "/profile/edit", component: ProfileEdit, meta: { requiresAuth: true } },
    { path: "/barcode/dashboard", component: BarcodeDashboard, meta: { requiresAuth: true } },
    { path: "/:pathMatch(.*)*", redirect: "/" }   // fallback
  ]
});

// redirect to login if not logged in
router.beforeEach(async (to, _from, next) => {
  if (!to.meta.requiresAuth) return next();

  const data = await userInfo();   // return user info if HttpOnly cookie is set
  if (data) {
    window.userInfo = data; // cache to global
    return next();         // already logged in
  }
  next("/login");                  // not logged in
});

export default router;
