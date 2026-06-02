import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, ref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';

import { useDailyLimit } from '@barcode/composables/useDailyLimit';

/**
 * useDailyLimit relies on onUnmounted, which only fires with an active component
 * instance. Mount a tiny harness whose setup() calls the composable and exposes
 * everything it returns so tests can drive it through `wrapper.vm`.
 */
function mountHarness(apiUpdate, showMessage) {
  const Harness = defineComponent({
    setup() {
      return useDailyLimit(apiUpdate, showMessage);
    },
    render() {
      return null;
    },
  });
  return mount(Harness);
}

// The debounced callback awaits the API promise internally. After advancing the
// 1000ms debounce timer we need to let those microtasks settle.
async function settle() {
  await flushPromises();
}

function makeBarcodesRef() {
  return ref([
    {
      barcode_uuid: 'u1',
      is_owned_by_current_user: true,
      daily_usage_limit: 0,
    },
  ]);
}

describe('useDailyLimit', () => {
  let apiUpdate;
  let showMessage;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    apiUpdate = vi.fn().mockResolvedValue({
      status: 'success',
      barcode: { daily_usage_limit: 10, usage_stats: {} },
    });
    showMessage = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('updateDailyLimit', () => {
    it('is a no-op when the barcode is not owned by the current user', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const foreign = { barcode_uuid: 'x', is_owned_by_current_user: false };

      await wrapper.vm.updateDailyLimit(foreign, 5, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).not.toHaveBeenCalled();
      expect(showMessage).not.toHaveBeenCalled();
    });

    it('is a no-op when no barcode is provided', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();

      await wrapper.vm.updateDailyLimit(null, 5, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).not.toHaveBeenCalled();
    });

    it('debounces two quick calls for the same barcode into a single API call', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 3, barcodes);
      vi.advanceTimersByTime(500);
      await wrapper.vm.updateDailyLimit(barcode, 7, barcodes);

      // First scheduled callback should have been cleared by the second call.
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledTimes(1);
      expect(apiUpdate).toHaveBeenCalledWith('u1', 7);
    });

    it('rejects a negative value without calling the API', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, -5, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).not.toHaveBeenCalled();
      expect(showMessage).toHaveBeenCalledWith('Daily limit must be 0 or greater', 'danger');
    });

    it('updates the matching barcode and reports success on a successful response', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 10, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 10);
      expect(barcodes.value[0].daily_usage_limit).toBe(10);
      expect(barcodes.value[0].usage_stats).toEqual({});
      expect(showMessage).toHaveBeenCalledWith('Daily limit set to 10', 'success');
    });

    it('reports an unlimited message when the value is 0', async () => {
      apiUpdate.mockResolvedValue({
        status: 'success',
        barcode: { daily_usage_limit: 0, usage_stats: { used: 0 } },
      });
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 0, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 0);
      expect(showMessage).toHaveBeenCalledWith('Daily limit set to unlimited', 'success');
    });

    it('toggles updatingLimit true while in-flight then false when settled', async () => {
      let resolveApi;
      apiUpdate.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveApi = resolve;
          })
      );
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 10, barcodes);
      vi.advanceTimersByTime(1000);
      // Let the debounce callback run up to the awaited API call.
      await Promise.resolve();

      expect(wrapper.vm.updatingLimit.u1).toBe(true);

      resolveApi({
        status: 'success',
        barcode: { daily_usage_limit: 10, usage_stats: {} },
      });
      await settle();

      expect(wrapper.vm.updatingLimit.u1).toBe(false);
    });

    it('reports a failure message when the API rejects', async () => {
      apiUpdate.mockRejectedValue(new Error('boom'));
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 10, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(showMessage).toHaveBeenCalledWith('Failed to update daily limit: boom', 'danger');
      expect(wrapper.vm.updatingLimit.u1).toBe(false);
    });

    it('does not mutate barcodes when the response status is not success', async () => {
      apiUpdate.mockResolvedValue({ status: 'error' });
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      await wrapper.vm.updateDailyLimit(barcode, 10, barcodes);
      vi.advanceTimersByTime(1000);
      await settle();

      expect(barcodes.value[0].daily_usage_limit).toBe(0);
      expect(showMessage).not.toHaveBeenCalledWith(expect.stringContaining('set to'), 'success');
    });
  });

  describe('incrementDailyLimit', () => {
    it('optimistically moves 0 -> 1 and schedules an update with the new value', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      wrapper.vm.incrementDailyLimit(barcode, barcodes);

      // Optimistic mutation happens synchronously.
      expect(barcode.daily_usage_limit).toBe(1);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 1);
    });

    it('increments a non-zero limit by one', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];
      barcode.daily_usage_limit = 4;

      wrapper.vm.incrementDailyLimit(barcode, barcodes);

      expect(barcode.daily_usage_limit).toBe(5);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 5);
    });
  });

  describe('decrementDailyLimit', () => {
    it('floors the optimistic value at 0', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      wrapper.vm.decrementDailyLimit(barcode, barcodes);

      expect(barcode.daily_usage_limit).toBe(0);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 0);
    });

    it('decrements a non-zero limit by one', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];
      barcode.daily_usage_limit = 3;

      wrapper.vm.decrementDailyLimit(barcode, barcodes);

      expect(barcode.daily_usage_limit).toBe(2);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 2);
    });
  });

  describe('toggleUnlimited', () => {
    it('moves 0 -> 1 and schedules an update', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      wrapper.vm.toggleUnlimited(barcode, barcodes);

      expect(barcode.daily_usage_limit).toBe(1);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 1);
    });

    it('moves a non-zero limit back to 0 (unlimited)', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];
      barcode.daily_usage_limit = 5;

      wrapper.vm.toggleUnlimited(barcode, barcodes);

      expect(barcode.daily_usage_limit).toBe(0);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 0);
    });
  });

  describe('toggleUnlimitedSwitch', () => {
    it('sets the limit to 0 when the switch is selected', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];
      barcode.daily_usage_limit = 8;

      wrapper.vm.toggleUnlimitedSwitch(barcode, { target: { selected: true } }, barcodes);

      expect(barcode.daily_usage_limit).toBe(0);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 0);
    });

    it('sets the limit to 1 when deselected from an unlimited (0) state', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      wrapper.vm.toggleUnlimitedSwitch(barcode, { target: { selected: false } }, barcodes);

      expect(barcode.daily_usage_limit).toBe(1);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 1);
    });
  });

  describe('applyLimitPreset', () => {
    it('applies a preset value and schedules an update', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      wrapper.vm.applyLimitPreset(barcode, 15, barcodes);

      expect(barcode.daily_usage_limit).toBe(15);

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).toHaveBeenCalledWith('u1', 15);
    });
  });

  describe('onUnmounted cleanup', () => {
    it('clears pending debounce timeouts so the API is never called after unmount', async () => {
      const wrapper = mountHarness(apiUpdate, showMessage);
      const barcodes = makeBarcodesRef();
      const barcode = barcodes.value[0];

      // Schedule a pending update but do NOT advance past the debounce yet.
      await wrapper.vm.updateDailyLimit(barcode, 10, barcodes);

      wrapper.unmount();

      vi.advanceTimersByTime(1000);
      await settle();

      expect(apiUpdate).not.toHaveBeenCalled();
    });
  });
});
