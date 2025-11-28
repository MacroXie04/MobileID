import { useServerWakeup } from '@shared/composables/useServerWakeup';
import '@/assets/styles/shared/server-wakeup.css';

export function useServerWakeupOverlaySetup() {
  const { isWakingUp, isChecking, elapsedSeconds, errorMessage, retryHealthCheck } =
    useServerWakeup();

  /**
   * Format elapsed seconds to mm:ss format
   */
  function formatElapsedTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Handle retry button click
   */
  async function handleRetry() {
    await retryHealthCheck();
  }

  return {
    isWakingUp,
    isChecking,
    elapsedSeconds,
    errorMessage,
    formatElapsedTime,
    handleRetry,
  };
}
