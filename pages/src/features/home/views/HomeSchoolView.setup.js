import { computed } from 'vue';
import { useHomeSchoolLogic } from '@home/composables/useHomeSchoolLogic.js';

// CSS Imports
import '@/assets/styles/home/HomeSchool.css';
// Import Font Awesome for this page (needed for GridMenu component)
import '@fortawesome/fontawesome-free/css/all.min.css';

// Components
import Header from '@school/components/Header.vue';
import UserProfile from '@school/components/UserProfile.vue';
import BarcodeDisplay from '@school/components/BarcodeDisplay.vue';
import GridMenu from '@school/components/GridMenu.vue';

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
