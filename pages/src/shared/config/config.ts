// Application configuration
// Prefer explicit Vite env variables and normalize trailing slashes.
// Note: Only variables prefixed with VITE_ are exposed to the client.
const normalizeBaseURL = (value) => value.replace(/\/+$/, '');

const getBaseURL = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    const configured =
      import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL_AWS || '';
    if (configured.trim()) {
      return normalizeBaseURL(configured.trim());
    }

    // In production we do not silently fall back to same-origin because that can
    // accidentally route traffic to an ALB endpoint.
    if (import.meta.env.PROD) {
      throw new Error('Missing VITE_API_BASE_URL in production build');
    }
  }

  // Default to localhost:8000 for local development
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  // Non-production fallback - empty string means same origin
  return '';
};

export const baseURL = getBaseURL();

export const config = {
  baseURL,
};

export default config;
