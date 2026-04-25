import 'vue-router';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    requiresActivation?: boolean;
    feature?: 'auth' | 'home' | 'dashboard';
  }
}
