import { useLoading } from '@shared/composables/useLoading';

export function useLoadingOverlaySetup() {
  const { isLoading, loadingMessage } = useLoading();

  return {
    isLoading,
    message: loadingMessage,
  };
}
