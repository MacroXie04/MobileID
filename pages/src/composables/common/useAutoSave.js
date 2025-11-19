import {onUnmounted, ref} from 'vue';

/**
 * Composable for auto-save functionality with debouncing
 * @param {Function} saveFunction - Async function to call for saving
 * @param {Object} options - Configuration options
 * @param {number} options.debounceMs - Debounce delay in milliseconds (default: 1500)
 * @param {number} options.successToastDuration - Success toast duration in ms (default: 3000)
 * @param {number} options.errorToastDuration - Error toast duration in ms (default: 5000)
 * @param {number} options.lastSavedDuration - Last saved indicator duration in ms (default: 5000)
 * @returns {Object} Auto-save functions and state
 */
export function useAutoSave(saveFunction, options = {}) {
    const {
        debounceMs = 1500,
        successToastDuration = 3000,
        errorToastDuration = 5000,
        lastSavedDuration = 5000
    } = options;

    // State
    const autoSaving = ref(false);
    const lastSaved = ref(false);
    const hasChanges = ref(false);
    const autoSaveTimer = ref(null);
    const lastSavedTimer = ref(null);
    const toastTimer = ref(null);

    const autoSaveStatus = ref({
        show: false,
        type: 'info', // 'info', 'success', 'error'
        message: ''
    });

    /**
     * Trigger auto-save after debounce delay
     */
    function triggerAutoSave() {
        hasChanges.value = true;
        lastSaved.value = false;

        // Clear previous timer
        if (autoSaveTimer.value) {
            clearTimeout(autoSaveTimer.value);
        }

        // Set new timer
        autoSaveTimer.value = setTimeout(() => {
            performAutoSave();
        }, debounceMs);
    }

    /**
     * Perform the actual auto-save operation
     */
    async function performAutoSave() {
        if (!hasChanges.value || autoSaving.value) return;

        autoSaving.value = true;

        try {
            const result = await saveFunction();

            if (result && result.success !== false) {
                hasChanges.value = false;
                lastSaved.value = true;

                // Show success toast
                showToast('success', result.message || 'Auto-saved successfully');

                // Hide last saved indicator after duration
                if (lastSavedTimer.value) {
                    clearTimeout(lastSavedTimer.value);
                }
                lastSavedTimer.value = setTimeout(() => {
                    lastSaved.value = false;
                }, lastSavedDuration);
            } else {
                // Show error toast
                showToast('error', result?.message || 'Auto-save failed');
            }
        } catch (error) {
            console.error('Auto-save error:', error);
            showToast('error', error.message || 'Auto-save failed: Network error');
        } finally {
            autoSaving.value = false;
        }
    }

    /**
     * Show toast notification
     * @param {string} type - Toast type: 'success' | 'error' | 'info'
     * @param {string} message - Toast message
     */
    function showToast(type, message) {
        autoSaveStatus.value = {
            show: true,
            type,
            message
        };

        // Clear previous toast timer
        if (toastTimer.value) {
            clearTimeout(toastTimer.value);
        }

        // Auto-hide toast
        const duration = type === 'error' ? errorToastDuration : successToastDuration;
        toastTimer.value = setTimeout(() => {
            autoSaveStatus.value.show = false;
        }, duration);
    }

    /**
     * Hide toast manually
     */
    function hideToast() {
        autoSaveStatus.value.show = false;
        if (toastTimer.value) {
            clearTimeout(toastTimer.value);
        }
    }

    /**
     * Get auto-save status text for display
     * @returns {string} Status text
     */
    function getStatusText() {
        if (autoSaving.value) {
            return 'Auto-saving...';
        } else if (lastSaved.value) {
            return 'Last saved: ' + new Date().toLocaleTimeString();
        } else if (hasChanges.value) {
            return 'Changes detected - auto-saving soon...';
        } else {
            return 'Auto-save enabled';
        }
    }

    /**
     * Mark that changes have been detected
     */
    function markChanged() {
        hasChanges.value = true;
        lastSaved.value = false;
    }

    /**
     * Force save immediately without debouncing
     */
    async function forceSave() {
        if (autoSaveTimer.value) {
            clearTimeout(autoSaveTimer.value);
        }
        await performAutoSave();
    }

    /**
     * Reset auto-save state
     */
    function reset() {
        hasChanges.value = false;
        lastSaved.value = false;
        autoSaving.value = false;
        autoSaveStatus.value.show = false;
    }

    // Cleanup on unmount
    onUnmounted(() => {
        if (autoSaveTimer.value) {
            clearTimeout(autoSaveTimer.value);
        }
        if (lastSavedTimer.value) {
            clearTimeout(lastSavedTimer.value);
        }
        if (toastTimer.value) {
            clearTimeout(toastTimer.value);
        }
    });

    return {
        // State
        autoSaving,
        lastSaved,
        hasChanges,
        autoSaveStatus,

        // Methods
        triggerAutoSave,
        performAutoSave,
        showToast,
        hideToast,
        getStatusText,
        markChanged,
        forceSave,
        reset,
    };
}
