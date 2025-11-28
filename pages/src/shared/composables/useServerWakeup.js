import { ref, readonly } from 'vue';
import { baseURL } from '@app/config/config';

// Singleton state - shared across all component instances
const isWakingUp = ref(false);
const isServerReady = ref(false);
const isChecking = ref(false);
const elapsedMs = ref(0);
const errorMessage = ref('');

// Configuration
const HEALTH_CHECK_TIMEOUT_MS = 3000; // 3 seconds initial timeout
const POLL_INTERVAL_MS = 2000; // Poll every 2 seconds

let pollingTimer = null;
let elapsedTimer = null;

/**
 * Check server health by calling the /health/ endpoint
 * @param {number} timeoutMs - Timeout in milliseconds
 * @returns {Promise<boolean>} - True if server is healthy
 */
async function checkServerHealth(timeoutMs = HEALTH_CHECK_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${baseURL}/health/`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return data.status === 'healthy';
    }
    return false;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      // Request timed out - likely cold start
      console.log('Health check timed out - server may be cold starting');
      return false;
    }

    // Network error or other issue
    console.error('Health check failed:', error.message);
    return false;
  }
}

/**
 * Start the elapsed time counter (updates every 10ms)
 */
function startElapsedTimer() {
  elapsedMs.value = 0;
  elapsedTimer = setInterval(() => {
    elapsedMs.value += 10;
  }, 10);
}

/**
 * Stop the elapsed time counter
 */
function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

/**
 * Stop polling for server health
 */
function stopPolling() {
  if (pollingTimer) {
    clearTimeout(pollingTimer);
    pollingTimer = null;
  }
  stopElapsedTimer();
}

/**
 * Poll for server health until it's ready or max retries reached
 * @param {boolean} shouldRefresh - Whether to refresh the page when server is ready
 * @returns {Promise<boolean>} - True if server became ready
 */
async function pollUntilReady(shouldRefresh = false) {
  return new Promise((resolve) => {
    const poll = async () => {
      const isHealthy = await checkServerHealth(5000); // Use longer timeout during polling

      if (isHealthy) {
        isServerReady.value = true;
        isWakingUp.value = false;
        stopPolling();

        // Refresh the page to ensure clean state after cold start
        if (shouldRefresh) {
          window.location.reload();
          return;
        }

        resolve(true);
        return;
      }

      pollingTimer = setTimeout(poll, POLL_INTERVAL_MS);
    };

    poll();
  });
}

/**
 * Wait for the server to be ready
 * Shows the wakeup overlay if the initial health check times out
 * Refreshes the page when server comes online after cold start
 * @returns {Promise<boolean>} - True if server is ready
 */
async function waitForServer() {
  // Prevent multiple simultaneous checks
  if (isChecking.value) {
    return isServerReady.value;
  }

  isChecking.value = true;
  errorMessage.value = '';

  try {
    // First, try a quick health check
    const isHealthy = await checkServerHealth();

    if (isHealthy) {
      isServerReady.value = true;
      isWakingUp.value = false;
      return true;
    }

    // Server didn't respond quickly - show wakeup overlay
    isWakingUp.value = true;
    isServerReady.value = false;
    startElapsedTimer();

    // Start polling until server is ready, then refresh the page
    return await pollUntilReady(true);
  } finally {
    isChecking.value = false;
  }
}

/**
 * Manually retry the server health check
 */
async function retryHealthCheck() {
  stopPolling();
  errorMessage.value = '';
  isWakingUp.value = true;
  startElapsedTimer();

  const isHealthy = await checkServerHealth(5000);

  if (isHealthy) {
    isServerReady.value = true;
    isWakingUp.value = false;
    stopPolling();
    // Refresh the page to ensure clean state
    window.location.reload();
    return true;
  }

  // Continue polling, then refresh when ready
  return await pollUntilReady(true);
}

/**
 * Reset state (for testing or when navigating away)
 */
function resetState() {
  stopPolling();
  isWakingUp.value = false;
  isServerReady.value = false;
  isChecking.value = false;
  elapsedMs.value = 0;
  errorMessage.value = '';
}

/**
 * Trigger server wakeup overlay (for API layer to call when server is unavailable)
 * Shows the wakeup overlay and starts polling for server health
 */
function triggerWakeup() {
  // Prevent triggering if already waking up or checking
  if (isWakingUp.value || isChecking.value) {
    return;
  }

  isWakingUp.value = true;
  isServerReady.value = false;
  errorMessage.value = '';
  startElapsedTimer();

  // Start polling until server is ready, then refresh the page
  pollUntilReady(true);
}

/**
 * Composable for server wakeup functionality
 */
export function useServerWakeup() {
  return {
    // State (readonly to prevent external mutations)
    isWakingUp: readonly(isWakingUp),
    isServerReady: readonly(isServerReady),
    isChecking: readonly(isChecking),
    elapsedMs: readonly(elapsedMs),
    errorMessage: readonly(errorMessage),

    // Methods
    checkServerHealth,
    waitForServer,
    retryHealthCheck,
    resetState,
    triggerWakeup,
  };
}
