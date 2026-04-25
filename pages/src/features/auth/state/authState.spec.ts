import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  setUserInfo,
  getUserInfo,
  clearUserInfo,
  isUserInfoStale,
  invalidateUserInfoCache,
  setApiError,
  getApiError,
} from '@auth';

describe('authState', () => {
  beforeEach(() => {
    clearUserInfo();
    setApiError(null);
  });

  describe('setUserInfo / getUserInfo', () => {
    it('should store and retrieve user info', () => {
      const user = { id: 1, username: 'testuser' };
      setUserInfo(user);
      expect(getUserInfo()).toEqual(user);
    });

    it('should return null when no user info is set', () => {
      expect(getUserInfo()).toBeNull();
    });

    it('should overwrite previous user info', () => {
      setUserInfo({ id: 1 });
      setUserInfo({ id: 2, username: 'updated' });
      expect(getUserInfo()).toEqual({ id: 2, username: 'updated' });
    });
  });

  describe('clearUserInfo', () => {
    it('should clear stored user info', () => {
      setUserInfo({ id: 1 });
      clearUserInfo();
      expect(getUserInfo()).toBeNull();
    });

    it('should reset timestamp so info is stale', () => {
      setUserInfo({ id: 1 });
      clearUserInfo();
      expect(isUserInfoStale()).toBe(true);
    });
  });

  describe('isUserInfoStale', () => {
    it('should be stale when no user info has been set', () => {
      expect(isUserInfoStale()).toBe(true);
    });

    it('should not be stale immediately after setting user info', () => {
      setUserInfo({ id: 1 });
      expect(isUserInfoStale()).toBe(false);
    });

    it('should be stale after TTL expires', () => {
      vi.useFakeTimers();
      setUserInfo({ id: 1 });
      // Advance past 5 minute TTL
      vi.advanceTimersByTime(5 * 60 * 1000 + 1);
      expect(isUserInfoStale()).toBe(true);
      vi.useRealTimers();
    });

    it('should not be stale just before TTL expires', () => {
      vi.useFakeTimers();
      setUserInfo({ id: 1 });
      vi.advanceTimersByTime(5 * 60 * 1000 - 100);
      expect(isUserInfoStale()).toBe(false);
      vi.useRealTimers();
    });
  });

  describe('invalidateUserInfoCache', () => {
    it('should make user info stale without clearing data', () => {
      setUserInfo({ id: 1, username: 'test' });
      invalidateUserInfoCache();
      expect(isUserInfoStale()).toBe(true);
      expect(getUserInfo()).toEqual({ id: 1, username: 'test' });
    });
  });

  describe('setApiError / getApiError', () => {
    it('should store and retrieve an API error', () => {
      const error = { message: 'Server error', status: 500 };
      setApiError(error);
      expect(getApiError()).toEqual(error);
    });

    it('should return null when no error is set', () => {
      expect(getApiError()).toBeNull();
    });

    it('should clear error when set to null', () => {
      setApiError('some error');
      setApiError(null);
      expect(getApiError()).toBeNull();
    });
  });
});
