import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { logout } from '@shared/api/auth';
import { useApi } from '@shared/composables/useApi';
import { useUserInfo } from '@user/composables/useUserInfo';

export function useHomeUserLogic() {
  const router = useRouter();
  const profile = ref(null);
  const barcodeDisplayRef = ref(null);

  // Use composables
  const { apiGenerateBarcode } = useApi();
  const { avatarSrc, loadAvatar } = useUserInfo();

  onMounted(() => {
    console.log('HomeUser component mounted');
    // read user info from window.userInfo
    const data = window.userInfo;
    console.log('window.userInfo:', data);
    profile.value = data?.profile;
    console.log('Profile set to:', profile.value);

    // Load user avatar
    loadAvatar();
  });

  async function handleGenerate() {
    const barcodeDisplay = barcodeDisplayRef.value;
    if (!barcodeDisplay) return;

    barcodeDisplay.startProcessing();

    try {
      const response = await apiGenerateBarcode();
      console.log('Generate barcode API response:', response);

      // Extract values from response
      const status = response?.status;
      const barcode = response?.barcode;
      const message = response?.message;

      console.log('Parsed values:', {
        status,
        barcode,
        message,
        hasBarcode: !!barcode,
        responseType: typeof response,
      });

      // Check if response is valid
      if (!response || typeof response !== 'object') {
        console.error('Invalid response format:', response);
        barcodeDisplay.showError('Invalid response from server');
        return;
      }

      if (status === 'success' && barcode) {
        console.log('Drawing barcode:', barcode);
        barcodeDisplay.drawPDF417(barcode);
        barcodeDisplay.showSuccess(message || 'Success');
      } else {
        console.warn('Barcode generation failed:', {
          status,
          barcode,
          message,
          fullResponse: response,
        });
        barcodeDisplay.showError(message || response?.detail || 'Server Error');
      }
    } catch (err) {
      // Handle different types of errors
      if (
        err.message.includes('Token refresh failed') ||
        err.message.includes('Max retries exceeded')
      ) {
        console.log('Token refresh failed or max retries exceeded, redirecting to login page');
        router.push('/login');
        return;
      } else if (err.message.includes('Network error')) {
        barcodeDisplay.showError('Network Error');
        console.error('Network error:', err.message);
      } else {
        barcodeDisplay.showError('Error');
        console.error('Barcode generation error:', err);
      }
    }
  }

  async function handleLogout() {
    try {
      await logout();

      // Clear window.userInfo
      window.userInfo = null;

      // Navigate to login
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout API fails, clear local data and redirect
      window.userInfo = null;
      router.push('/login');
    }
  }

  return {
    profile,
    barcodeDisplayRef,
    avatarSrc,
    handleGenerate,
    handleLogout,
  };
}
