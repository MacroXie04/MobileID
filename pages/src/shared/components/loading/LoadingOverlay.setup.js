import { useLoading } from '@shared/composables/api/useLoading';

export function useLoadingOverlaySetup() {
  const { isLoading, loadingMessage } = useLoading();

  return {
    isLoading,
    message: loadingMessage,
  };
}
