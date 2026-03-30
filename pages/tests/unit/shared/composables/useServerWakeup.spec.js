import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@app/config/config', () => ({
  baseURL: 'https://api.example.com',
}));

import { useServerWakeup } from '@shared/composables/useServerWakeup';

describe('useServerWakeup', () => {
  let wakeup;

  beforeEach(() => {
    vi.useFakeTimers();
    global.fetch = vi.fn();
    wakeup = useServerWakeup();
    wakeup.resetState();
  });

  afterEach(() => {
    wakeup.resetState();
    vi.useRealTimers();
    delete global.fetch;
  });

  describe('checkServerHealth', () => {
    it('should return true when server responds with healthy status', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' }),
      });

      const result = await wakeup.checkServerHealth();

      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/health/',
        expect.objectContaining({
          method: 'GET',
          headers: { Accept: 'application/json' },
        })
      );
    });

    it('should return false when server responds with non-ok status', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
      });

      const result = await wakeup.checkServerHealth();
      expect(result).toBe(false);
    });

    it('should return false when server responds with unhealthy status', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'unhealthy' }),
      });

      const result = await wakeup.checkServerHealth();
      expect(result).toBe(false);
    });

    it('should return false on network error', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await wakeup.checkServerHealth();
      expect(result).toBe(false);
    });

    it('should return false on abort/timeout', async () => {
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      global.fetch.mockRejectedValueOnce(abortError);

      const result = await wakeup.checkServerHealth();
      expect(result).toBe(false);
    });
  });

  describe('waitForServer', () => {
    it('should return true immediately if server is healthy', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' }),
      });

      const result = await wakeup.waitForServer();

      expect(result).toBe(true);
      expect(wakeup.isServerReady.value).toBe(true);
      expect(wakeup.isWakingUp.value).toBe(false);
    });

    it('should trigger wakeup overlay when initial health check fails', async () => {
      // Health check fails
      global.fetch.mockResolvedValueOnce({ ok: false });
      // Polling will also fail to keep things simple
      global.fetch.mockResolvedValue({ ok: false });

      // Start waitForServer (don't await — it polls indefinitely until healthy)
      wakeup.waitForServer();

      // Let the initial health check promise resolve
      await vi.advanceTimersByTimeAsync(100);

      // After the initial check fails, wakeup overlay should show
      expect(wakeup.isWakingUp.value).toBe(true);
      expect(wakeup.isServerReady.value).toBe(false);

      // Clean up polling
      wakeup.resetState();
    });

    it('should prevent multiple simultaneous checks', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' }),
      });

      const promise1 = wakeup.waitForServer();
      const promise2 = wakeup.waitForServer();

      await promise1;

      // Second call should return current state without re-checking
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('triggerWakeup', () => {
    it('should set wakeup state', () => {
      // Mock fetch for polling
      global.fetch.mockResolvedValue({
        ok: false,
      });

      wakeup.triggerWakeup();

      expect(wakeup.isWakingUp.value).toBe(true);
      expect(wakeup.isServerReady.value).toBe(false);
    });

    it('should not trigger if already waking up', () => {
      global.fetch.mockResolvedValue({ ok: false });

      wakeup.triggerWakeup();
      const fetchCountAfterFirst = global.fetch.mock.calls.length;

      wakeup.triggerWakeup();

      // Should not make additional fetch calls
      expect(global.fetch.mock.calls.length).toBe(fetchCountAfterFirst);
    });
  });

  describe('resetState', () => {
    it('should reset all state values', () => {
      global.fetch.mockResolvedValue({ ok: false });
      wakeup.triggerWakeup();

      wakeup.resetState();

      expect(wakeup.isWakingUp.value).toBe(false);
      expect(wakeup.isServerReady.value).toBe(false);
      expect(wakeup.isChecking.value).toBe(false);
      expect(wakeup.elapsedMs.value).toBe(0);
      expect(wakeup.errorMessage.value).toBe('');
    });
  });

  describe('elapsed timer', () => {
    it('should track elapsed time during wakeup', async () => {
      global.fetch.mockResolvedValue({ ok: false });

      wakeup.triggerWakeup();

      vi.advanceTimersByTime(500);
      expect(wakeup.elapsedMs.value).toBeGreaterThan(0);

      wakeup.resetState();
      expect(wakeup.elapsedMs.value).toBe(0);
    });
  });
});
