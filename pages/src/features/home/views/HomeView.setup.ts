import { computed, onMounted, ref } from 'vue';
import { getUserInfo, getApiError } from '@auth';
import { useHomeLogic } from '@home/composables/useHomeLogic';
import { BarcodeDisplay, GridMenu, Header, UserProfile } from '@mobile-id';
import '@home/styles/HomeShell.css';
import '@home/styles/Home.css';

export { Header, UserProfile, BarcodeDisplay, GridMenu };

export function useHomeViewSetup() {
  const pageLoading = ref(true);
  const apiError = ref(null);

  const {
    profile,
    avatarSrc,
    loading: homeLoading,
    serverStatus,
    barcodeDisplayRef,
    isRefreshingToken,
    scannerDetectionEnabled,
    preferFrontCamera,
    handleGenerate,
    initializeHome,
  } = useHomeLogic();

  const isDetectionActive = computed(() => {
    return barcodeDisplayRef.value?.isDetectionActive ?? false;
  });

  const isBarcodeVisible = computed(() => {
    return barcodeDisplayRef.value?.isBarcodeVisible ?? false;
  });

  const scannerDetected = computed(() => {
    return barcodeDisplayRef.value?.scannerDetected ?? false;
  });

  onMounted(async () => {
    // Check if API error occurred (connection failed)
    const storedError = getApiError();
    if (storedError) {
      apiError.value = storedError;
      pageLoading.value = false;
      return;
    }

    // If user info exists, we're good — show the home view
    const data = getUserInfo();
    if (!data) {
      apiError.value = 'Unable to load user data';
      pageLoading.value = false;
      return;
    }

    await initializeHome();
    pageLoading.value = false;
  });

  // Retry connection function
  function retryConnection() {
    window.location.reload();
  }

  return {
    pageLoading,
    apiError,
    retryConnection,
    profile,
    avatarSrc,
    homeLoading,
    serverStatus,
    barcodeDisplayRef,
    isRefreshingToken,
    scannerDetectionEnabled,
    preferFrontCamera,
    handleGenerate,
    isDetectionActive,
    isBarcodeVisible,
    scannerDetected,
  };
}
