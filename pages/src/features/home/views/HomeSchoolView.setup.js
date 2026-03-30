import { computed } from 'vue';
import { useHomeSchoolLogic } from '@home/composables/useHomeSchoolLogic.js';

// CSS Imports
import '@/assets/styles/home/HomeSchool.css';

// Components
import Header from '@/features/header/Header.vue';
import UserProfile from '@/features/user-profile/UserProfile.vue';
import BarcodeDisplay from '@/features/barcode-display/BarcodeDisplay.vue';
import GridMenu from '@/features/grid-menu/GridMenu.vue';

export { Header, UserProfile, BarcodeDisplay, GridMenu };

export function useHomeSchoolViewSetup() {
  const {
    profile,
    avatarSrc,
    loading,
    serverStatus,
    barcodeDisplayRef,
    isRefreshingToken,
    scannerDetectionEnabled,
    preferFrontCamera,
    handleGenerate,
  } = useHomeSchoolLogic();

  // Get detection state from BarcodeDisplay component
  const isDetectionActive = computed(() => {
    return barcodeDisplayRef.value?.isDetectionActive ?? false;
  });

  const scannerDetected = computed(() => {
    return barcodeDisplayRef.value?.scannerDetected ?? false;
  });

  return {
    profile,
    avatarSrc,
    loading,
    serverStatus,
    barcodeDisplayRef,
    isRefreshingToken,
    scannerDetectionEnabled,
    preferFrontCamera,
    handleGenerate,
    isDetectionActive,
    scannerDetected,
  };
}
