import { ref } from 'vue';

/**
 * Shared camera permission state - singleton pattern
 * This ensures camera permission state is synchronized across all components
 */
const hasCameraPermission = ref(false);
const isCheckingPermission = ref(false);
const permissionDenied = ref(false);

// Check existing permission on module load
checkExistingPermission();

/**
 * Check if camera permission was already granted using Permissions API
 * @returns {Promise<boolean>} True if permission is granted
 */
async function checkExistingPermission() {
  if (isCheckingPermission.value) return hasCameraPermission.value;

  isCheckingPermission.value = true;
  try {
    // Use Permissions API to check camera status
    if (navigator.permissions && navigator.permissions.query) {
      const result = await navigator.permissions.query({ name: 'camera' });
      if (result.state === 'granted') {
        hasCameraPermission.value = true;
        permissionDenied.value = false;
      } else if (result.state === 'denied') {
        hasCameraPermission.value = false;
        permissionDenied.value = true;
      }

      // Listen for permission changes
      result.addEventListener('change', () => {
        if (result.state === 'granted') {
          hasCameraPermission.value = true;
          permissionDenied.value = false;
        } else if (result.state === 'denied') {
          hasCameraPermission.value = false;
          permissionDenied.value = true;
        } else {
          hasCameraPermission.value = false;
          permissionDenied.value = false;
        }
      });
    }
  } catch (_err) {
    // Permissions API may not be supported, that's ok
    console.log('Permissions API not supported, will check on request');
  } finally {
    isCheckingPermission.value = false;
  }
  return hasCameraPermission.value;
}

/**
 * Request and ensure camera permission
 * @param {Object} options - Options for camera request
 * @param {string} options.facingMode - 'user' for front camera, 'environment' for back camera
 * @param {boolean} options.stopStream - Whether to stop stream after permission granted (default: true)
 * @returns {Promise<{granted: boolean, stream: MediaStream|null, error: string|null}>} Permission result
 */
async function ensureCameraPermission(options = {}) {
  const { facingMode = 'environment', stopStream = false } = options;

  try {
    if (!navigator?.mediaDevices?.getUserMedia) {
      return { granted: false, stream: null, error: 'Camera not supported' };
    }

    const constraints = {
      video: {
        facingMode,
        width: { ideal: 640 },
        height: { ideal: 480 },
      },
    };

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    hasCameraPermission.value = true;
    permissionDenied.value = false;

    // Optionally stop stream immediately after getting permission
    if (stopStream) {
      stream.getTracks().forEach((t) => t.stop());
      return { granted: true, stream: null, error: null };
    }

    return { granted: true, stream, error: null };
  } catch (err) {
    console.error('Camera permission error:', err);
    hasCameraPermission.value = false;
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      permissionDenied.value = true;
    }
    return { granted: false, stream: null, error: err.message };
  }
}

/**
 * Composable for shared camera permission state
 * @returns {Object} Camera permission state and methods
 */
export function useCameraPermission() {
  return {
    hasCameraPermission,
    isCheckingPermission,
    permissionDenied,
    checkExistingPermission,
    ensureCameraPermission,
  };
}
