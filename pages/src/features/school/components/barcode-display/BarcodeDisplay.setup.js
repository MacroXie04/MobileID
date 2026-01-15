import { ref, watch, onMounted, onUnmounted } from 'vue';

import '@material/web/icon/icon';

// CSS
import '@/assets/styles/school/school-merged.css';

// Composable
import { useScannerDetection } from '@school/composables/useScannerDetection.js';

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

export const emitsDefinition = ['generate', 'scanner-detected'];

export function useSchoolBarcodeDisplaySetup({ props, emit } = {}) {
  const componentProps = props ?? {
    scannerDetectionEnabled: false,
    preferFrontCamera: true,
  };
  const emitFn = emit ?? (() => {});

  // Template refs
  const barcodeCanvas = ref(null);
  const videoElement = ref(null);
  const detectionCanvas = ref(null);

  // State
  const showBarcode = ref(false);
  const progressPercent = ref(100);
  const autoDisplayed = ref(false);
  let progressInterval = null;
  let autoDisplayTimeout = null;

  // Methods (defined ahead for composable)
  function handleDetectionError(error) {
    console.error('Detection error:', error);
  }

  function handleScannerDetected(objects) {
    console.log('Scanner detected:', objects);

    // Pause detection while barcode is displayed
    stopDetection();

    autoDisplayed.value = true;

    emitFn('scanner-detected', objects);
    // Emit 'generate' event to trigger parent's handleGenerate()
    // The parent will handle barcode generation and animation consistently
    emitFn('generate');

    // Clear auto-display notice after 3 seconds
    if (autoDisplayTimeout) {
      clearTimeout(autoDisplayTimeout);
    }
    autoDisplayTimeout = setTimeout(() => {
      autoDisplayed.value = false;
    }, 3000);
  }

  // Scanner detection composable - pass refs for direct binding
  const {
    isDetectionActive,
    isModelLoading,
    hasCameraPermission,
    startDetection,
    stopDetection,
    ensureCameraPermission,
  } = useScannerDetection({
    preferFrontCamera: componentProps.preferFrontCamera,
    onDetected: handleScannerDetected,
    onError: handleDetectionError,
    videoRef: videoElement,
    canvasRef: detectionCanvas,
  });

  function startProgressBar() {
    progressPercent.value = 100;

    if (progressInterval) {
      clearInterval(progressInterval);
    }

    const duration = 10000; // 10 seconds
    const interval = 100; // Update every 100ms
    const decrement = 100 / (duration / interval);

    progressInterval = setInterval(() => {
      progressPercent.value -= decrement;
      if (progressPercent.value <= 0) {
        progressPercent.value = 0;
        clearInterval(progressInterval);
        showBarcode.value = false;
        // Note: Resume detection is handled by parent's handleGenerate()
      }
    }, interval);
  }

  // Auto-start detection when enabled
  async function initDetection() {
    if (componentProps.scannerDetectionEnabled) {
      // Request permission and start detection automatically
      // ensureCameraPermission from useScannerDetection returns boolean
      const granted = await ensureCameraPermission();
      if (granted) {
        await startDetection();
      }
    }
  }

  // Watch for prop changes
  watch(
    () => componentProps.scannerDetectionEnabled,
    async (enabled) => {
      if (enabled) {
        await initDetection();
      } else if (isDetectionActive.value) {
        stopDetection();
      }
    }
  );

  watch(
    () => componentProps.preferFrontCamera,
    async () => {
      if (isDetectionActive.value) {
        // Restart detection with new camera preference
        stopDetection();
        await startDetection();
      }
    }
  );

  // Lifecycle
  onMounted(async () => {
    // Auto-start detection if enabled
    if (componentProps.scannerDetectionEnabled) {
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        initDetection();
      }, 500);
    }
  });

  onUnmounted(() => {
    if (progressInterval) {
      clearInterval(progressInterval);
    }
    if (autoDisplayTimeout) {
      clearTimeout(autoDisplayTimeout);
    }
    stopDetection();
  });

  const exposeBindings = {
    barcodeCanvas,
    showBarcode,
    startProgressBar,
    isDetectionActive,
    scannerDetected: autoDisplayed,
    startDetection,
  };

  return {
    barcodeCanvas,
    videoElement,
    detectionCanvas,
    showBarcode,
    progressPercent,
    isDetectionActive,
    isModelLoading,
    hasCameraPermission,
    exposeBindings,
  };
}
