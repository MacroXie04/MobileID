import { toRefs } from 'vue';
import { useRouter } from 'vue-router';
import { logout } from '@auth';
import { clearAuthCookies, clearAuthStorage } from '@shared/utils/cookie';

// CSS
import '@mobile-id/styles/mobile-id.css';

export const propsDefinition = {
  serverStatus: {
    type: String,
    default: 'Emergency',
  },
  scannerDetectionEnabled: {
    type: Boolean,
    default: false,
  },
  isDetectionActive: {
    type: Boolean,
    default: false,
  },
  scannerDetected: {
    type: Boolean,
    default: false,
  },
};

export function useGridMenuSetup(args: any = {}) {
  const { props } = args;
  const router = useRouter();
  const componentProps = props ?? {};
  const { serverStatus } = toRefs(componentProps);

  function handleEditProfile() {
    router.push('/profile/edit');
  }

  function handleBarcodeDashboard() {
    router.push('/dashboard');
  }

  async function handleLogout() {
    try {
      // Call logout API
      await logout();

      // Clear authentication data
      clearAuthCookies();
      clearAuthStorage();

      // Clear user profile cache
      try {
        const { clearUserProfile } = await import('@profile');
        clearUserProfile();
      } catch (error) {
        console.warn('Could not clear user profile cache:', error);
      }

      // Redirect to login page
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Even if API call fails, still clear local data and redirect
      clearAuthCookies();
      clearAuthStorage();
      router.push('/login');
    }
  }

  return {
    serverStatus,
    handleEditProfile,
    handleBarcodeDashboard,
    handleLogout,
  };
}
