// Application configuration
// Use Vite env for base URL; fall back to localhost for local dev.
// Note: Only variables prefixed with VITE_ are exposed to the client.
export const baseURL =
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
    'http://127.0.0.1:8000';

export const config = {
    baseURL
};

export default config;