import { baseURL } from '@app/config/config';
import { getCookie } from '@shared/utils/cookie';

let inflightPromise = null;

/**
 * Ensure a CSRF cookie exists and return its value.
 * Only issues one network request at a time to avoid thundering herd.
 */
export async function ensureCsrfToken() {
  const existing = getCookie('csrftoken');
  if (existing) return existing;

  if (!inflightPromise) {
    inflightPromise = fetch(`${baseURL}/authn/csrf/`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(async (res) => {
        // Attempt to read token from cookie; fall back to response body.
        const fromCookie = getCookie('csrftoken');
        if (fromCookie) return fromCookie;

        const ct = res.headers?.get('content-type') || '';
        if (ct.includes('application/json')) {
          try {
            const data = await res.json();
            return getCookie('csrftoken') || data?.csrfToken || '';
          } catch {
            return getCookie('csrftoken') || '';
          }
        }
        return '';
      })
      .catch(() => '')
      .finally(() => {
        inflightPromise = null;
      });
  }

  return inflightPromise;
}
