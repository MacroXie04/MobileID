import '@/assets/styles/dashboard/BarcodeDashboard.css';

import { useDevicesLogic } from '@dashboard/composables/useDevicesLogic';

/**
 * Setup function for DevicesCard component.
 * Provides device management logic and state.
 */
export function useDevicesCardSetup() {
  const {
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
  } = useDevicesLogic();

  /**
   * Handle single device revocation.
   * @param {number} deviceId - The token ID to revoke
   */
  async function handleRevoke(deviceId) {
    await revokeDevice(deviceId);
  }

  /**
   * Handle revoking all other devices.
   */
  async function handleRevokeAll() {
    await revokeAllOtherDevices();
  }

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
    handleRevoke,
    handleRevokeAll,
  };
}
