import { useServerWakeup } from '@shared/composables/useServerWakeup';
import '@/assets/styles/shared/server-wakeup.css';

export function useServerWakeupOverlaySetup() {
  const { isWakingUp, isChecking, elapsedMs, errorMessage, retryHealthCheck } = useServerWakeup();

  /**
   * Format elapsed milliseconds to mm:ss.mmm format (milliseconds)
   */
  function formatElapsedTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    const milliseconds = Math.floor(ms % 1000);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
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
    elapsedMs,
    errorMessage,
    formatElapsedTime,
    handleRetry,
  };
}
