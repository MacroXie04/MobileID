import { ref, watch } from 'vue';
import { userInfo } from '@auth';
import { getUserInfo, setUserInfo } from '@auth';
import { useToken } from '@auth';
import { useUserInfo } from '@profile';
import { useBarcodeApi } from '@barcode';

export function useHomeLogic() {
  // State
  const loading = ref(false);
  const serverStatus = ref('Emergency');
  const barcodeDisplayRef = ref(null);

  // Scanner detection settings (fetched from backend)
  const scannerDetectionEnabled = ref(false);
  const preferFrontCamera = ref(true);

  // Use composables
  const { profile, avatarSrc: defaultAvatarSrc, loadAvatar, loadUserProfile } = useUserInfo();
  const { isRefreshingToken } = useToken();
  const { apiGenerateBarcode, apiGetActiveProfile, apiGetBarcodeDashboard } = useBarcodeApi();

  // Create a new ref for avatarSrc that can be overridden
  const avatarSrc = ref(defaultAvatarSrc.value);

  // Watch for changes in defaultAvatarSrc
  watch(defaultAvatarSrc, (newValue) => {
    avatarSrc.value = newValue;
  });

  /**
   * Refresh user profile and active profile data
   */
  async function refreshProfileData(forceRefresh = false) {
    // Refresh cached auth state if it was cleared or force refresh is requested
    const cached = getUserInfo();
    if (!cached || forceRefresh) {
      try {
        const data = await userInfo();
        if (data) {
          setUserInfo(data);
          if (data.profile) {
            profile.value = data.profile;
          }
        }
      } catch (error) {
        console.error('Home: Failed to refresh user info:', error);
      }
    } else if (cached && cached.profile) {
      // Update profile from cached auth state
      profile.value = cached.profile;
    }

    // Force reload user profile to get latest data
    try {
      await loadUserProfile(forceRefresh);
    } catch (error) {
      console.error('Home: Failed to reload user profile:', error);
    }

    // Load user avatar
    await loadAvatar();

    // Check for active profile (for School users with barcode profile association)
    try {
      const response = await apiGetActiveProfile();

      if (response && response.profile_info) {
        // Override with barcode profile info
        profile.value = {
          name: response.profile_info.name,
          information_id: response.profile_info.information_id,
        };

        // Update avatar if provided
        if (response.profile_info.avatar_data) {
          avatarSrc.value = response.profile_info.avatar_data;
        }
      }
    } catch (error) {
      console.error('Home: Failed to load active profile:', error);
    }
  }

  async function handleGenerate() {
    loading.value = true;
    serverStatus.value = 'Processing';

    try {
      const { status, barcode, message, profile_info } = await apiGenerateBarcode();
      serverStatus.value = message || 'Success';

      if (status === 'success' && barcode) {
        // Update profile if profile_info is returned (for School users with associate_user_profile_with_barcode)
        if (profile_info) {
          profile.value = {
            name: profile_info.name,
            information_id: profile_info.information_id,
          };
          // Update avatar if provided
          if (profile_info.avatar_data) {
            avatarSrc.value = profile_info.avatar_data;
          }
        }

        const barcodeDisplay = barcodeDisplayRef.value;
        if (!barcodeDisplay || typeof barcodeDisplay.renderBarcodeSequence !== 'function') {
          serverStatus.value = 'Unable to display barcode';
          return;
        }

        try {
          await barcodeDisplay.renderBarcodeSequence(barcode, {
            displayDuration: 10000,
          });
        } catch (error) {
          serverStatus.value = 'Unable to display barcode';

          if (
            scannerDetectionEnabled.value &&
            typeof barcodeDisplay.startDetection === 'function'
          ) {
            await barcodeDisplay.startDetection();
          }

          console.error('Home: Failed to render barcode:', error);
          return;
        }

        // Reset server status back to Emergency after animation completes
        serverStatus.value = 'Emergency';

        // Resume scanner detection if enabled
        if (scannerDetectionEnabled.value && barcodeDisplayRef.value) {
          // Access the startDetection method from the component's exposeBindings
          const startDetection = barcodeDisplayRef.value?.startDetection;
          if (typeof startDetection === 'function') {
            await startDetection();
          }
        }
      } else {
        serverStatus.value = message || 'Error';
      }
    } catch (err) {
      // Handle different types of errors
      if (
        err.message.includes('Token refresh failed') ||
        err.message.includes('Max retries exceeded')
      ) {
        console.log('Token refresh failed or max retries exceeded, redirecting to login page');
        return;
      } else if (err.message.includes('Network error')) {
        serverStatus.value = 'Network Error';
        console.error('Network error:', err.message);
      } else {
        serverStatus.value = 'Error';
        console.error('Barcode generation error:', err);
      }
    } finally {
      loading.value = false;
    }
  }

  /**
   * Load scanner detection settings from backend
   */
  async function loadScannerSettings() {
    try {
      const data = await apiGetBarcodeDashboard();
      if (data && data.settings) {
        scannerDetectionEnabled.value = Boolean(data.settings.scanner_detection_enabled);
        preferFrontCamera.value =
          data.settings.prefer_front_camera !== undefined
            ? Boolean(data.settings.prefer_front_camera)
            : true;
      }
    } catch (error) {
      console.error('Home: Failed to load scanner settings:', error);
    }
  }

  async function initializeHome() {
    await Promise.all([refreshProfileData(), loadScannerSettings()]);
  }

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
    initializeHome,
  };
}
