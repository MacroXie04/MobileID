import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';

// Mock Vue lifecycle hooks
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue');
  return {
    ...actual,
    onUnmounted: vi.fn(),
  };
});

import { useAutoSave } from '@shared/composables/useAutoSave';

describe('useAutoSave', () => {
  let saveFn;

  beforeEach(() => {
    vi.useFakeTimers();
    saveFn = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should have correct default state', () => {
      const { autoSaving, lastSaved, hasChanges, autoSaveStatus } = useAutoSave(saveFn);
      expect(autoSaving.value).toBe(false);
      expect(lastSaved.value).toBe(false);
      expect(hasChanges.value).toBe(false);
      expect(autoSaveStatus.value).toEqual({ show: false, type: 'info', message: '' });
    });
  });

  describe('triggerAutoSave', () => {
    it('should set hasChanges and call save after debounce', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { triggerAutoSave, hasChanges } = useAutoSave(saveFn, { debounceMs: 500 });

      triggerAutoSave();
      expect(hasChanges.value).toBe(true);
      expect(saveFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(500);
      await vi.runAllTimersAsync();

      expect(saveFn).toHaveBeenCalledOnce();
    });

    it('should debounce rapid calls', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { triggerAutoSave } = useAutoSave(saveFn, { debounceMs: 500 });

      triggerAutoSave();
      vi.advanceTimersByTime(200);
      triggerAutoSave();
      vi.advanceTimersByTime(200);
      triggerAutoSave();
      vi.advanceTimersByTime(500);
      await vi.runAllTimersAsync();

      expect(saveFn).toHaveBeenCalledOnce();
    });
  });

  describe('performAutoSave', () => {
    it('should show success toast on successful save', async () => {
      saveFn.mockResolvedValue({ success: true, message: 'Saved!' });
      const { performAutoSave, markChanged, autoSaveStatus, hasChanges, lastSaved } =
        useAutoSave(saveFn);

      markChanged();
      await performAutoSave();

      expect(hasChanges.value).toBe(false);
      expect(lastSaved.value).toBe(true);
      expect(autoSaveStatus.value.show).toBe(true);
      expect(autoSaveStatus.value.type).toBe('success');
      expect(autoSaveStatus.value.message).toBe('Saved!');
    });

    it('should show error toast on failed save', async () => {
      saveFn.mockResolvedValue({ success: false, message: 'Failed to save' });
      const { performAutoSave, markChanged, autoSaveStatus } = useAutoSave(saveFn);

      markChanged();
      await performAutoSave();

      expect(autoSaveStatus.value.show).toBe(true);
      expect(autoSaveStatus.value.type).toBe('error');
      expect(autoSaveStatus.value.message).toBe('Failed to save');
    });

    it('should show error toast on exception', async () => {
      saveFn.mockRejectedValue(new Error('Network error'));
      const { performAutoSave, markChanged, autoSaveStatus } = useAutoSave(saveFn);

      markChanged();
      await performAutoSave();

      expect(autoSaveStatus.value.type).toBe('error');
      expect(autoSaveStatus.value.message).toBe('Network error');
    });

    it('should not call save when there are no changes', async () => {
      const { performAutoSave } = useAutoSave(saveFn);
      await performAutoSave();
      expect(saveFn).not.toHaveBeenCalled();
    });

    it('should handle skipped saves silently', async () => {
      saveFn.mockResolvedValue({ skipped: true });
      const { performAutoSave, markChanged, hasChanges, autoSaveStatus } = useAutoSave(saveFn);

      markChanged();
      await performAutoSave();

      expect(hasChanges.value).toBe(false);
      expect(autoSaveStatus.value.show).toBe(false);
    });

    it('should not call save concurrently when already saving', async () => {
      let resolveFirst;
      saveFn.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          })
      );

      const { performAutoSave, markChanged, autoSaving } = useAutoSave(saveFn);

      markChanged();
      const firstSave = performAutoSave();
      expect(autoSaving.value).toBe(true);

      // Second call while saving should return early without calling saveFn again
      markChanged();
      performAutoSave();
      expect(saveFn).toHaveBeenCalledTimes(1);

      resolveFirst({ success: true });
      await firstSave;
    });

    it('should skip queued save when no changes remain after save completes', async () => {
      let resolveFirst;
      saveFn.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          })
      );

      const { performAutoSave, markChanged } = useAutoSave(saveFn, { debounceMs: 100 });

      markChanged();
      const firstSave = performAutoSave();

      // Call performAutoSave again while in progress — sets queuedSave
      markChanged();
      performAutoSave();

      // First save succeeds and clears hasChanges
      resolveFirst({ success: true });
      await firstSave;

      // queuedSave was true but hasChanges became false from the success handler
      // so no re-save should be triggered
      vi.advanceTimersByTime(200);
      await vi.runAllTimersAsync();

      expect(saveFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('forceSave', () => {
    it('should save immediately without debouncing', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { forceSave, markChanged } = useAutoSave(saveFn, { debounceMs: 5000 });

      markChanged();
      await forceSave();

      expect(saveFn).toHaveBeenCalledOnce();
    });

    it('should cancel pending debounced save', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { triggerAutoSave, forceSave } = useAutoSave(saveFn, { debounceMs: 5000 });

      triggerAutoSave();
      await forceSave();
      vi.advanceTimersByTime(5000);

      expect(saveFn).toHaveBeenCalledOnce();
    });
  });

  describe('showToast / hideToast', () => {
    it('should auto-hide success toast after duration', async () => {
      const { showToast, autoSaveStatus } = useAutoSave(saveFn, { successToastDuration: 1000 });

      showToast('success', 'Saved');
      expect(autoSaveStatus.value.show).toBe(true);

      vi.advanceTimersByTime(1000);
      expect(autoSaveStatus.value.show).toBe(false);
    });

    it('should auto-hide error toast after error duration', async () => {
      const { showToast, autoSaveStatus } = useAutoSave(saveFn, { errorToastDuration: 2000 });

      showToast('error', 'Failed');
      expect(autoSaveStatus.value.show).toBe(true);

      vi.advanceTimersByTime(2000);
      expect(autoSaveStatus.value.show).toBe(false);
    });

    it('should hide toast manually', () => {
      const { showToast, hideToast, autoSaveStatus } = useAutoSave(saveFn);

      showToast('info', 'Test');
      expect(autoSaveStatus.value.show).toBe(true);

      hideToast();
      expect(autoSaveStatus.value.show).toBe(false);
    });
  });

  describe('getStatusText', () => {
    it('should return "Auto-save enabled" when idle', () => {
      const { getStatusText } = useAutoSave(saveFn);
      expect(getStatusText()).toBe('Auto-save enabled');
    });

    it('should indicate changes detected', () => {
      const { getStatusText, markChanged } = useAutoSave(saveFn);
      markChanged();
      expect(getStatusText()).toBe('Changes detected - auto-saving soon...');
    });

    it('should show last saved time after save', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { getStatusText, performAutoSave, markChanged } = useAutoSave(saveFn);
      markChanged();
      await performAutoSave();
      expect(getStatusText()).toContain('Last saved:');
    });
  });

  describe('reset', () => {
    it('should reset all state', async () => {
      saveFn.mockResolvedValue({ success: true });
      const { reset, markChanged, performAutoSave, hasChanges, lastSaved, autoSaveStatus } =
        useAutoSave(saveFn);

      markChanged();
      await performAutoSave();
      reset();

      expect(hasChanges.value).toBe(false);
      expect(lastSaved.value).toBe(false);
      expect(autoSaveStatus.value.show).toBe(false);
    });
  });
});
