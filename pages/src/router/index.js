import {createRouter, createWebHistory} from "vue-router";
import {userInfo} from "@/api/auth";

const Login = () => import("@/views/authn/Login.vue");
const Home = () => import("@/views/home/Home.vue");
const ProfileEdit = () => import("@/views/ProfileEdit.vue");
const Register = () => import("@/views/authn/Register.vue");
const BarcodeDashboard = () => import("@/views/BarcodeDashboard.vue");

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {path: "/login", component: Login},
        {path: "/register", component: Register},
        {path: "/", component: Home, meta: {requiresAuth: true}},
        {path: "/profile/edit", component: ProfileEdit, meta: {requiresAuth: true}},
        {path: "/dashboard", component: BarcodeDashboard, meta: {requiresAuth: true}},
        // Catch-all 404: redirect authenticated users to home, others to login
        {path: "/:pathMatch(.*)*", redirect: (to) => ({path: "/"})}
    ]
});

// Global auth guard: checks meta.requiresAuth and caches user info in a single place
router.beforeEach(async (to, _from, next) => {
    try {
        if (!to.meta.requiresAuth) return next();

        // If already cached, check access
        if (window.userInfo) {
            // Check if User type trying to access barcode dashboard
            if (to.path === '/dashboard' && window.userInfo.groups && window.userInfo.groups.includes('User')) {
                return next({path: "/"});
            }
            return next();
        }

        const data = await userInfo();
        if (data) {
            window.userInfo = data;
            // Check if User type trying to access barcode dashboard
            if (to.path === '/dashboard' && data.groups && data.groups.includes('User')) {
                return next({path: "/"});
            }
            return next();
        }
        return next({path: "/login", query: {redirect: to.fullPath}});
    } catch (_err) {
        window.apiError = "API server is offline";
        // If navigating to a protected route but API is down, still allow to hit Home which shows an error panel.
        return next();
    }
});

export default router;
