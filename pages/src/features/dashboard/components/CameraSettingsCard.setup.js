import { computed, ref, watch, onUnmounted } from 'vue';
import { useScannerDetection } from '@school/composables/useScannerDetection.js';

// CSS - use shared dashboard styles
import '@/assets/styles/dashboard/BarcodeDashboard.css';

export const propsDefinition = {
  scannerDetectionEnabled: {
    type: Boolean,
    default: false,
  },
  preferFrontCamera: {
    type: Boolean,
    default: true,
  },
};

export const emitsDefinition = ['update-scanner-detection', 'update-prefer-front-camera'];

export function useCameraSettingsCardSetup({ props } = {}) {
  const componentProps = props ?? {
    scannerDetectionEnabled: false,
    preferFrontCamera: true,
  };

  // Template refs
  const videoElement = ref(null);
  const detectionCanvas = ref(null);

  // Permission state
  const isRequestingPermission = ref(false);
  const permissionDenied = ref(false);

  // Scanner detection composable
  const {
    isDetectionActive,
    isModelLoading,
    detectionStatus,
    cameras,
    selectedCameraId,
    detectedObjects,
    hasCameraPermission,
    startDetection,
    stopDetection,
    toggleDetection: toggleDetectionBase,
    switchCamera,
    ensureCameraPermission,
  } = useScannerDetection({
    preferFrontCamera: componentProps.preferFrontCamera,
    onDetected: (objects) => {
      console.log('CameraSettings: Scanner detected:', objects);
    },
    onError: (error) => {
      console.error('CameraSettings: Detection error:', error);
    },
    videoRef: videoElement,
    canvasRef: detectionCanvas,
  });

  // Computed
  const statusClass = computed(() => {
    if (isModelLoading.value) return 'loading';
    if (isDetectionActive.value) return 'active';
    return 'inactive';
  });

  const statusIcon = computed(() => {
    if (isModelLoading.value) return 'hourglass_empty';
    if (isDetectionActive.value) return 'videocam';
    return 'videocam_off';
  });

  // Methods
  async function requestCameraPermission() {
    isRequestingPermission.value = true;
    permissionDenied.value = false;

    try {
      const { granted } = await ensureCameraPermission();
      if (!granted) {
        permissionDenied.value = true;
      }
    } catch (error) {
      console.error('Permission request error:', error);
      permissionDenied.value = true;
    } finally {
      isRequestingPermission.value = false;
    }
  }

  async function toggleDetection() {
    await toggleDetectionBase();
  }

  function handleCameraChange(event) {
    const cameraId = event.target.value;
    switchCamera(cameraId);
  }

  function formatCameraLabel(camera) {
    if (camera.label) {
      const label = camera.label;
      if (label.length > 20) {
        return label.substring(0, 17) + '...';
      }
      return label;
    }
    return `Camera ${cameras.value.indexOf(camera) + 1}`;
  }

  // Stop detection when disabled
  watch(
    () => componentProps.scannerDetectionEnabled,
    (enabled) => {
      if (!enabled && isDetectionActive.value) {
        stopDetection();
      }
    }
  );

  // Cleanup
  onUnmounted(() => {
    stopDetection();
  });

  return {
    videoElement,
    detectionCanvas,
    isRequestingPermission,
    permissionDenied,
    isDetectionActive,
    isModelLoading,
    detectionStatus,
    cameras,
    selectedCameraId,
    detectedObjects,
    hasCameraPermission,
    requestCameraPermission,
    toggleDetection,
    handleCameraChange,
    formatCameraLabel,
    statusClass,
    statusIcon,
  };
}
