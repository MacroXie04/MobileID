import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearAuthCookies,
  clearAuthStorage,
  getCookie,
  hasAuthTokens,
} from '@shared/utils/cookie';

const clearAllCookies = () => {
  document.cookie.split(';').forEach((cookie) => {
    const name = cookie.split('=')[0]?.trim();
    if (name) {
      document.cookie = `${name}=; Max-Age=0; Path=/;`;
    }
  });
};

describe('cookie utils', () => {
  beforeEach(() => {
    clearAllCookies();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('gets cookie values by name', () => {
    document.cookie = 'csrftoken=abc123; Secure';

    expect(getCookie('csrftoken')).toBe('abc123');
    expect(getCookie('missing')).toBe('');
  });

  it('clears auth cookies while leaving other cookies intact', () => {
    document.cookie = 'csrftoken=token; Secure';
    document.cookie = 'sessionid=session; Secure';
    document.cookie = 'access_token=access; Secure';
    document.cookie = 'refresh_token=refresh; Secure';
    document.cookie = 'non_auth=keep';

    clearAuthCookies();

    expect(getCookie('csrftoken')).toBe('');
    expect(getCookie('sessionid')).toBe('');
    expect(getCookie('access_token')).toBe('');
    expect(getCookie('refresh_token')).toBe('');
    expect(getCookie('non_auth')).toBe('keep');
  });

  it('clears auth tokens from storage including access and refresh keys', () => {
    localStorage.setItem('access_token', 'access');
    localStorage.setItem('user_info', 'user');
    localStorage.setItem('access', 'old-access');
    localStorage.setItem('refresh', 'old-refresh');
    sessionStorage.setItem('refresh_token', 'refresh');
    sessionStorage.setItem('auth_token', 'auth');

    clearAuthStorage();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user_info')).toBeNull();
    expect(localStorage.getItem('access')).toBeNull();
    expect(localStorage.getItem('refresh')).toBeNull();
    expect(sessionStorage.getItem('refresh_token')).toBeNull();
    expect(sessionStorage.getItem('auth_token')).toBeNull();
  });

  describe('hasAuthTokens', () => {
    it('returns false when no auth indicators present', () => {
      expect(hasAuthTokens()).toBe(false);
    });

    it('returns true when csrftoken cookie is present', () => {
      document.cookie = 'csrftoken=abc123; Secure';
      expect(hasAuthTokens()).toBe(true);
    });

    it('does not depend on feature auth state', () => {
      localStorage.setItem('user_info', JSON.stringify({ profile: { name: 'Test' } }));
      expect(hasAuthTokens()).toBe(false);
    });

    it('returns false after clearing csrftoken', () => {
      document.cookie = 'csrftoken=abc123; Secure';
      expect(hasAuthTokens()).toBe(true);

      clearAllCookies();
      expect(hasAuthTokens()).toBe(false);
    });
  });
});
