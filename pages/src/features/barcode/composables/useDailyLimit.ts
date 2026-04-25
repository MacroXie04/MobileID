/**
 * Composable for managing barcode daily usage limits
 * Handles updating, incrementing, decrementing, and toggling limits with debouncing
 */

import { onUnmounted, ref } from 'vue';

export function useDailyLimit(apiUpdateBarcodeDailyLimit, showMessage) {
  // Per-barcode daily limit updating state
  const updatingLimit = ref<Record<string, any>>({});

  // Per-barcode debounce timeouts
  const dailyLimitTimeouts = new Map();

  /**
   * Update daily usage limit for a barcode with debouncing
   * @param {Object} barcode - Barcode object
   * @param {number} value - New daily limit value (0 = unlimited)
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  async function updateDailyLimit(barcode, value, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;

    // Clear previous timeout for this specific barcode
    if (dailyLimitTimeouts.has(barcode.barcode_uuid)) {
      clearTimeout(dailyLimitTimeouts.get(barcode.barcode_uuid));
    }

    // Debounce for 1 second per barcode
    const timeoutId = setTimeout(async () => {
      dailyLimitTimeouts.delete(barcode.barcode_uuid);
      try {
        const limit = parseInt(value) || 0;
        if (limit < 0) {
          showMessage('Daily limit must be 0 or greater', 'danger');
          return;
        }

        updatingLimit.value = { ...updatingLimit.value, [barcode.barcode_uuid]: true };
        const res = await apiUpdateBarcodeDailyLimit(barcode.barcode_uuid, limit);

        if (res?.status === 'success' && res?.barcode) {
          // Update local barcode data
          const idx = barcodes.value.findIndex((b) => b.barcode_uuid === barcode.barcode_uuid);
          if (idx !== -1) {
            barcodes.value[idx] = {
              ...barcodes.value[idx],
              daily_usage_limit: res.barcode.daily_usage_limit,
              usage_stats: res.barcode.usage_stats,
            };
          }
          showMessage(`Daily limit set to ${limit === 0 ? 'unlimited' : limit}`, 'success');
        }
      } catch (e) {
        showMessage('Failed to update daily limit: ' + (e?.message || 'Unknown error'), 'danger');
      } finally {
        updatingLimit.value = { ...updatingLimit.value, [barcode.barcode_uuid]: false };
      }
    }, 1000);
    dailyLimitTimeouts.set(barcode.barcode_uuid, timeoutId);
  }

  /**
   * Increment daily limit by 1
   * @param {Object} barcode - Barcode object
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  function incrementDailyLimit(barcode, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    const current = Number(barcode.daily_usage_limit || 0);
    const next = current === 0 ? 1 : current + 1;
    // Optimistic UI update
    barcode.daily_usage_limit = next;
    updateDailyLimit(barcode, next, barcodes);
  }

  /**
   * Decrement daily limit by 1 (minimum 0)
   * @param {Object} barcode - Barcode object
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  function decrementDailyLimit(barcode, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    const current = Number(barcode.daily_usage_limit || 0);
    const next = Math.max(0, current - 1);
    barcode.daily_usage_limit = next;
    updateDailyLimit(barcode, next, barcodes);
  }

  /**
   * Toggle between unlimited (0) and limited (1)
   * @param {Object} barcode - Barcode object
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  function toggleUnlimited(barcode, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    const next = Number(barcode.daily_usage_limit || 0) === 0 ? 1 : 0;
    barcode.daily_usage_limit = next;
    updateDailyLimit(barcode, next, barcodes);
  }

  /**
   * Handle switch toggle from UI component
   * @param {Object} barcode - Barcode object
   * @param {Event} event - Switch event with selected property
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  function toggleUnlimitedSwitch(barcode, event, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    const selected = Boolean(event?.target?.selected);
    const next = selected
      ? 0
      : Number(barcode.daily_usage_limit || 0) === 0
        ? 1
        : Number(barcode.daily_usage_limit);
    barcode.daily_usage_limit = next;
    updateDailyLimit(barcode, next, barcodes);
  }

  /**
   * Apply preset limit value
   * @param {Object} barcode - Barcode object
   * @param {number} value - Preset value to apply
   * @param {Array} barcodes - Array of barcodes to update (reactive)
   */
  function applyLimitPreset(barcode, value, barcodes) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    const limit = Math.max(0, Number(value) || 0);
    barcode.daily_usage_limit = limit === 0 ? 0 : limit;
    updateDailyLimit(barcode, limit, barcodes);
  }

  /**
   * Clean up timeout on unmount
   */
  onUnmounted(() => {
    for (const timeoutId of dailyLimitTimeouts.values()) {
      clearTimeout(timeoutId);
    }
    dailyLimitTimeouts.clear();
  });

  return {
    updatingLimit,
    updateDailyLimit,
    incrementDailyLimit,
    decrementDailyLimit,
    toggleUnlimited,
    toggleUnlimitedSwitch,
    applyLimitPreset,
  };
}
