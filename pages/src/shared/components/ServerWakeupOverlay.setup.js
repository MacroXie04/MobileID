import { useServerWakeup } from '@shared/composables/useServerWakeup';
import '@/assets/styles/shared/server-wakeup.css';

export function useServerWakeupOverlaySetup() {
  const { isWakingUp, isChecking, elapsedMs, errorMessage, retryHealthCheck } = useServerWakeup();

  /**
   * Format elapsed milliseconds to mm:ss.cc format (centiseconds)
   */
  function formatElapsedTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    const centiseconds = Math.floor((ms % 1000) / 10);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;
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
