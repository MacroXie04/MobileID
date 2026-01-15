import { onMounted } from 'vue';
import ServerWakeupOverlay from '@shared/components/server-wakeup/ServerWakeupOverlay.vue';
import LoadingOverlay from '@shared/components/loading/LoadingOverlay.vue';
import { useServerWakeup } from '@shared/composables/useServerWakeup';

export { ServerWakeupOverlay, LoadingOverlay };

export function useAppSetup() {
  const { waitForServer } = useServerWakeup();

  onMounted(async () => {
    // Check server health on app mount
    // This will show the wakeup overlay if the server is cold starting
    await waitForServer();
  });
}
