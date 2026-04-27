import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue';

import '@material/web/icon/icon.js';

// CSS
import '@mobile-id/styles/mobile-id.css';

// Composable
import { usePdf417 } from '@barcode';
import { useScannerDetection } from '@shared/composables/device/useScannerDetection';

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

export function useMobileIdBarcodeDisplaySetup(args: any = {}) {
  const { props, emit } = args;
  const componentProps = props ?? {
    scannerDetectionEnabled: false,
    preferFrontCamera: true,
  };
  const emitFn = emit ?? (() => {});

  // Template refs
  const barcodeCanvas = ref<HTMLCanvasElement | null>(null);
  const videoElement = ref<HTMLVideoElement | null>(null);
  const detectionCanvas = ref<HTMLCanvasElement | null>(null);

  // State
  const showBarcode = ref(false);
  const progressPercent = ref(100);
  const autoDisplayed = ref(false);
  const renderError = ref('');
  let progressInterval: ReturnType<typeof setInterval> | null = null;
  let autoDisplayTimeout: ReturnType<typeof setTimeout> | null = null;

  // Methods (defined ahead for composable)
  function handleDetectionError(error: unknown) {
    console.error('Detection error:', error);
  }

  function handleScannerDetected(objects: unknown[]) {
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
  const { drawPdf417 } = usePdf417();

  function clearProgressBar() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  function resetDisplayState() {
    clearProgressBar();
    progressPercent.value = 100;
    showBarcode.value = false;
  }

  function startProgressBar(duration = 10000, onComplete: () => void = () => {}) {
    progressPercent.value = 100;
    clearProgressBar();
    const interval = 100; // Update every 100ms
    const decrement = 100 / (duration / interval);

    progressInterval = setInterval(() => {
      progressPercent.value -= decrement;
      if (progressPercent.value <= 0) {
        progressPercent.value = 0;
        clearProgressBar();
        showBarcode.value = false;
        onComplete();
      }
    }, interval);
  }

  async function renderBarcodeSequence(
    data: string,
    options: { displayDuration?: number; moduleWidth?: number; moduleHeight?: number } = {}
  ) {
    const { displayDuration = 10000, moduleWidth = 2.5, moduleHeight = 1 } = options;

    if (!data) {
      renderError.value = 'Unable to display barcode';
      throw new Error('Barcode data is required');
    }

    stopDetection();
    renderError.value = '';
    resetDisplayState();

    await nextTick();

    try {
      await drawPdf417(barcodeCanvas.value, data, {
        moduleWidth,
        moduleHeight,
      });
    } catch (error) {
      renderError.value = 'Unable to display barcode';
      resetDisplayState();
      throw error;
    }

    showBarcode.value = true;

    return new Promise<void>((resolve) => {
      startProgressBar(displayDuration, () => resolve());
    });
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
    clearProgressBar();
    if (autoDisplayTimeout) {
      clearTimeout(autoDisplayTimeout);
    }
    stopDetection();
  });

  const exposeBindings = {
    isDetectionActive,
    isBarcodeVisible: showBarcode,
    renderBarcodeSequence,
    scannerDetected: autoDisplayed,
    startDetection,
  };

  return {
    barcodeCanvas,
    videoElement,
    detectionCanvas,
    showBarcode,
    progressPercent,
    renderError,
    isDetectionActive,
    isModelLoading,
    hasCameraPermission,
    exposeBindings,
  };
}
