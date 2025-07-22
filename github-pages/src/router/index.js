import { createRouter, createWebHistory } from "vue-router";
import { userInfo } from "@/api/auth";

const Login = () => import("@/views/Login.vue");
const Home  = () => import("@/views/Home.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: Login },
    { path: "/",      component: Home,  meta: { requiresAuth: true } },
    { path: "/:pathMatch(.*)*", redirect: "/" }   // 兜底
  ]
});

// ≈≈≈ 路由守卫：仅检测“是否已登录” ≈≈≈
router.beforeEach(async (to, _from, next) => {
  if (!to.meta.requiresAuth) return next();

  const data = await userInfo();   // 有 HttpOnly cookie 时才返回用户信息
  if (data) return next();         // 已登录
  next("/login");                  // 未登录
});

export default router;
