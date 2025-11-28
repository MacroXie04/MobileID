import { ref, readonly } from 'vue';

// Singleton state - shared across all component instances
const isLoading = ref(false);
const loadingMessage = ref('');
let activeRequests = 0;

/**
 * Composable for global loading state management
 */
export function useLoading() {
  /**
   * Start loading state
   * @param {string} message - Optional loading message to display
   */
  function startLoading(message = 'Loading...') {
    activeRequests++;
    isLoading.value = true;
    loadingMessage.value = message;
  }

  /**
   * Stop loading state
   * Decrements the active requests counter and only hides
   * the loading overlay when all requests are complete
   */
  function stopLoading() {
    activeRequests = Math.max(0, activeRequests - 1);
    if (activeRequests === 0) {
      isLoading.value = false;
      loadingMessage.value = '';
    }
  }

  /**
   * Force stop all loading
   * Use this to immediately hide the loading overlay
   */
  function forceStopLoading() {
    activeRequests = 0;
    isLoading.value = false;
    loadingMessage.value = '';
  }

  /**
   * Set loading message without changing loading state
   * @param {string} message - Message to display
   */
  function setLoadingMessage(message) {
    loadingMessage.value = message;
  }

  return {
    // State (readonly to prevent external mutations)
    isLoading: readonly(isLoading),
    loadingMessage: readonly(loadingMessage),

    // Methods
    startLoading,
    stopLoading,
    forceStopLoading,
    setLoadingMessage,
  };
}
