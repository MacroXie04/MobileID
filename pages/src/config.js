// Application configuration
// Use Vite env for base URL; fall back to Nginx proxy path in production.
// Note: Only variables prefixed with VITE_ are exposed to the client.
export const baseURL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'https://mobileid-49975674882.us-central1.run.app/';

export const config = {
  baseURL,
};

export default config;
