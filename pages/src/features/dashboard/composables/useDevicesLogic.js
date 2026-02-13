import { computed, onMounted, ref } from 'vue';
import { useApi } from '@shared/composables/useApi';

/**
 * Composable for managing user devices/sessions.
 * Provides functionality to list and display logged-in devices.
 */
export function useDevicesLogic() {
  const { apiCallWithAutoRefresh } = useApi();

  // Reactive state
  const devices = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const revoking = ref(null); // token_id being revoked, or 'all'

  /**
   * Fetch all devices/sessions for the current user.
   */
  async function fetchDevices() {
    loading.value = true;
    error.value = null;

    try {
      // The backend identifies the current device using the access token's iat claim
      // which is automatically included in the authenticated request
      const response = await apiCallWithAutoRefresh('/authn/devices/', {
        method: 'GET',
      });

      // Handle null/undefined response gracefully
      if (response && Array.isArray(response.devices)) {
        devices.value = response.devices;
      } else if (response && typeof response === 'object') {
        devices.value = response.devices || [];
      } else {
        devices.value = [];
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
      error.value = err.message || 'Failed to load devices';
      devices.value = [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * Get the appropriate icon name for a device type.
   * @param {string} deviceType - desktop/mobile/tablet/unknown
   * @returns {string} Material icon name
   */
  function getDeviceIcon(deviceType) {
    switch (deviceType) {
      case 'mobile':
        return 'smartphone';
      case 'tablet':
        return 'tablet';
      case 'desktop':
        return 'computer';
      default:
        return 'devices';
    }
  }

  /**
   * Format a date string to relative time (e.g., "2 hours ago").
   * @param {string} dateString - ISO date string
   * @returns {string} Relative time string
   */
  function formatRelativeTime(dateString) {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  /**
   * Format expiration time to show when re-login is required.
   * @param {string} dateString - ISO date string of expiration
   * @returns {string} Formatted expiration info
   */
  function formatExpirationTime(dateString) {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date - now;

    // Already expired
    if (diffMs <= 0) {
      return 'Expired';
    }

    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) {
      return `Expires in ${diffMins} minute${diffMins !== 1 ? 's' : ''}`;
    } else if (diffHours < 24) {
      return `Expires in ${diffHours} hour${diffHours !== 1 ? 's' : ''}`;
    } else {
      return `Expires in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
    }
  }

  /**
   * Format a date to readable date/time string.
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date
   */
  function formatDateTime(dateString) {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * Revoke a specific device/session.
   * @param {number} tokenId - The token ID to revoke
   */
  async function revokeDevice(tokenId) {
    revoking.value = tokenId;
    try {
      await apiCallWithAutoRefresh(`/authn/devices/${tokenId}/revoke/`, {
        method: 'DELETE',
      });
      await fetchDevices();
    } catch (err) {
      console.error('Failed to revoke device:', err);
      error.value = err.message || 'Failed to log out device';
    } finally {
      revoking.value = null;
    }
  }

  /**
   * Revoke all other devices/sessions except the current one.
   */
  async function revokeAllOtherDevices() {
    revoking.value = 'all';
    try {
      await apiCallWithAutoRefresh('/authn/devices/revoke-all/', {
        method: 'DELETE',
      });
      await fetchDevices();
    } catch (err) {
      console.error('Failed to revoke all devices:', err);
      error.value = err.message || 'Failed to log out other devices';
    } finally {
      revoking.value = null;
    }
  }

  // Computed properties
  const currentDevice = computed(() => {
    return devices.value.find((d) => d.is_current) || null;
  });

  const otherDevices = computed(() => {
    return devices.value.filter((d) => !d.is_current);
  });

  const hasOtherDevices = computed(() => {
    return otherDevices.value.length > 0;
  });

  const deviceCount = computed(() => {
    return devices.value.length;
  });

  // Lifecycle
  onMounted(() => {
    fetchDevices();
  });

  return {
    // State
    devices,
    loading,
    error,
    revoking,

    // Computed
    currentDevice,
    otherDevices,
    hasOtherDevices,
    deviceCount,

    // Methods
    fetchDevices,
    revokeDevice,
    revokeAllOtherDevices,
    getDeviceIcon,
    formatRelativeTime,
    formatExpirationTime,
    formatDateTime,
  };
}
