import { createRouter, createWebHistory } from "vue-router";
import { userInfo } from "@/api/auth";

const Login = () => import("@/views/Login.vue");
const HomeSchool = () => import("@/views/HomeSchool.vue");
const HomeUser = () => import("@/views/HomeUser.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/school", component: HomeSchool, meta: { requiresAuth: true, allow: ["School"] } },
    { path: "/user", component: HomeUser, meta: { requiresAuth: true, allow: ["User"] } },
    { path: "/", redirect: to => "/" }
  ]
});

let cache = null;

router.beforeEach(async (to, _from, next) => {
  if (!cache) cache = await userInfo();

  const loggedIn = !!cache;
  const groups = cache?.groups || [];

  if (to.path === "/") {
    if (!loggedIn) return next("/login");
    if (groups.includes("School")) return next("/school");
    if (groups.includes("User")) return next("/user");
    return next("/login");
  }

  if (to.meta.requiresAuth) {
    if (!loggedIn) return next("/login");
    if (!groups.some(g => to.meta.allow.includes(g))) return next("/login");
  }

  next();
});

export default router;
