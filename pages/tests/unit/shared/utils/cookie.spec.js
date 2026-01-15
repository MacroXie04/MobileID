import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearAuthCookies,
  clearAuthStorage,
  getCookie,
  hasAuthTokens,
} from '@shared/utils/cookie.js';

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
    document.cookie = 'csrftoken=abc123';

    expect(getCookie('csrftoken')).toBe('abc123');
    expect(getCookie('missing')).toBe('');
  });

  it('clears auth cookies while leaving other cookies intact', () => {
    document.cookie = 'csrftoken=token';
    document.cookie = 'sessionid=session';
    document.cookie = 'access_token=access';
    document.cookie = 'refresh_token=refresh';
    document.cookie = 'non_auth=keep';

    clearAuthCookies();

    expect(getCookie('csrftoken')).toBe('');
    expect(getCookie('sessionid')).toBe('');
    expect(getCookie('access_token')).toBe('');
    expect(getCookie('refresh_token')).toBe('');
    expect(getCookie('non_auth')).toBe('keep');
  });

  it('clears auth tokens from storage', () => {
    localStorage.setItem('access_token', 'access');
    localStorage.setItem('user_info', 'user');
    sessionStorage.setItem('refresh_token', 'refresh');
    sessionStorage.setItem('auth_token', 'auth');

    clearAuthStorage();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user_info')).toBeNull();
    expect(sessionStorage.getItem('refresh_token')).toBeNull();
    expect(sessionStorage.getItem('auth_token')).toBeNull();
  });

  it('detects auth tokens in cookies or storage', () => {
    expect(hasAuthTokens()).toBe(false);

    document.cookie = 'sessionid=session';
    expect(hasAuthTokens()).toBe(true);

    clearAllCookies();
    expect(hasAuthTokens()).toBe(false);

    document.cookie = 'access_token=access';
    expect(hasAuthTokens()).toBe(true);

    clearAllCookies();
    localStorage.setItem('access_token', 'access');
    expect(hasAuthTokens()).toBe(true);
  });
});
