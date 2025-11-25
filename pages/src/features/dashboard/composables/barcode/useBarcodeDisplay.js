import { computed, ref } from 'vue';

/**
 * Composable for managing barcode display state and UI
 * Handles loading, success, error states and progress bar
 * @returns {Object} Display state and control functions
 */
export function useBarcodeDisplay() {
  // State
  const isProcessing = ref(false);
  const successMessage = ref('');
  const errorMessage = ref('');
  const barcodeDisplayed = ref(false);
  const buttonMessage = ref('PAY / Check-in');
  const progressValue = ref(100);
  const showProgressBar = ref(false);

  // Progress interval reference
  let progressInterval = null;

  // Computed
  const buttonIcon = computed(() => {
    if (successMessage.value) return 'check_circle';
    if (errorMessage.value) return 'error';
    if (isProcessing.value) return 'hourglass_empty';
    return 'contactless';
  });

  /**
   * Clear barcode container content
   * @param {string} containerId - ID of the container element
   */
  function clearBarcodeContainer(containerId = 'barcode-container') {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = '';
    }
  }

  /**
   * Reset all UI state to initial values
   */
  function resetUI() {
    // Clear any running intervals
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }

    isProcessing.value = false;
    barcodeDisplayed.value = false;
    successMessage.value = '';
    errorMessage.value = '';
    buttonMessage.value = 'PAY / Check-in';
    progressValue.value = 100;
    showProgressBar.value = false;
  }

  /**
   * Set UI to processing state
   * @param {string} message - Optional processing message
   */
  function startProcessing(message = 'Processing...') {
    resetUI();
    isProcessing.value = true;
    buttonMessage.value = message;
  }

  /**
   * Set UI to success state with countdown
   * @param {string} message - Success message to display
   * @param {number} duration - Duration in milliseconds (default: 10000)
   */
  function showSuccess(message = 'Success', duration = 10000) {
    isProcessing.value = false;
    successMessage.value = message;
    buttonMessage.value = message;
    barcodeDisplayed.value = true;
    progressValue.value = 100;
    showProgressBar.value = true;

    // Start countdown
    const interval = 100; // Update every 100ms
    const decrement = (interval / duration) * 100;

    // Clear any existing interval
    if (progressInterval) {
      clearInterval(progressInterval);
    }

    progressInterval = setInterval(() => {
      progressValue.value -= decrement;

      if (progressValue.value <= 0) {
        clearInterval(progressInterval);
        progressInterval = null;
        if (barcodeDisplayed.value) {
          resetUI();
        }
      }
    }, interval);
  }

  /**
   * Set UI to error state
   * @param {string} message - Error message to display
   * @param {number} duration - Duration to show error in milliseconds (default: 4000)
   */
  function showError(message = 'Error', duration = 4000) {
    isProcessing.value = false;
    errorMessage.value = message;
    buttonMessage.value = message;

    // Auto-reset after duration
    setTimeout(() => {
      if (errorMessage.value) {
        resetUI();
      }
    }, duration);
  }

  /**
   * Manually trigger barcode hiding
   */
  function hideBarcode() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
    resetUI();
  }

  return {
    // State
    isProcessing,
    successMessage,
    errorMessage,
    barcodeDisplayed,
    buttonMessage,
    progressValue,
    showProgressBar,
    buttonIcon,

    // Methods
    clearBarcodeContainer,
    resetUI,
    startProcessing,
    showSuccess,
    showError,
    hideBarcode,
  };
}
