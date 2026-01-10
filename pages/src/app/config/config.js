// Application configuration
// Use Vite env for base URL; fall back to localhost:8000 for local development.
// Note: Only variables prefixed with VITE_ are exposed to the client.
const getBaseURL = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Default to localhost:8000 for local development
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  // Production fallback - empty string means same origin
  return '';
};

export const baseURL = getBaseURL();

export const config = {
  baseURL,
};

export default config;
