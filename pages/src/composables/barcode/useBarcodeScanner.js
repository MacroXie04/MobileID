import {nextTick, onUnmounted, ref, watch} from 'vue';

/**
 * Composable for handling barcode/QR code scanning functionality
 * Uses ZXing library for barcode detection
 * @param {Object} options - Configuration options
 * @param {Function} options.onScan - Callback when barcode is scanned
 * @param {Function} options.onError - Callback when error occurs
 * @returns {Object} Scanner functions and state
 */
export function useBarcodeScanner(options = {}) {
    const {onScan, onError} = options;

    // State
    const showScanner = ref(false);
    const scanning = ref(false);
    const scannerStatus = ref('Position the barcode within the camera view');
    const videoRef = ref(null);
    const cameras = ref([]);
    const selectedCameraId = ref(null);
    const hasCameraPermission = ref(false);

    // Internal state
    let codeReader = null;

    /**
     * Check and request camera permission
     * @returns {Promise<boolean>} True if permission granted
     */
    async function ensureCameraPermission() {
        try {
            if (!navigator?.mediaDevices?.getUserMedia) {
                scannerStatus.value = 'Camera is not supported in this browser.';
                return false;
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                video: {facingMode: 'environment'}
            });

            // Stop the stream immediately after getting permission
            stream.getTracks().forEach(t => t.stop());
            hasCameraPermission.value = true;
            return true;
        } catch (err) {
            console.error('Camera permission error:', err);
            hasCameraPermission.value = false;
            scannerStatus.value = 'Camera permission denied.';
            return false;
        }
    }

    /**
     * Initialize and start the scanner
     */
    async function startScanner() {
        try {
            scanning.value = true;
            scannerStatus.value = 'Initializing scanner...';

            // Dynamically import ZXing library
            const {BrowserMultiFormatReader} = await import('@zxing/library');
            codeReader = new BrowserMultiFormatReader();

            // Request camera permission if not already granted
            if (!hasCameraPermission.value) {
                const granted = await ensureCameraPermission();
                if (!granted) {
                    scannerStatus.value = 'Camera permission denied.';
                    scanning.value = false;
                    if (onError) {
                        onError(new Error('Camera permission denied'));
                    }
                    return;
                }
            }

            // Get available cameras
            if (cameras.value.length === 0) {
                const videoInputDevices = await codeReader.listVideoInputDevices();
                cameras.value = videoInputDevices;

                if (videoInputDevices.length > 0) {
                    // Select first camera by default
                    if (!selectedCameraId.value) {
                        selectedCameraId.value = videoInputDevices[0].deviceId;
                    }
                } else {
                    scannerStatus.value = 'No cameras found.';
                    scanning.value = false;
                    if (onError) {
                        onError(new Error('No cameras found'));
                    }
                    return;
                }
            }

            if (!selectedCameraId.value) {
                scannerStatus.value = 'No camera selected.';
                scanning.value = false;
                return;
            }

            scannerStatus.value = 'Position the barcode within the camera view';

            // Start decoding from video device
            codeReader.decodeFromVideoDevice(
                selectedCameraId.value,
                videoRef.value,
                (result, error) => {
                    if (result) {
                        const code = result.getText();
                        if (onScan) {
                            onScan(code);
                        }
                        stopScanner();
                    }
                    // Ignore errors during scanning (they're usually just "no barcode found")
                }
            );
        } catch (error) {
            console.error('Scanner start error:', error);
            scannerStatus.value = `Failed to start scanner: ${error.message}`;
            scanning.value = false;
            if (onError) {
                onError(error);
            }
        }
    }

    /**
     * Stop the scanner and release resources
     */
    function stopScanner() {
        if (codeReader) {
            codeReader.reset();
            codeReader = null;
        }
        showScanner.value = false;
        scanning.value = false;
        scannerStatus.value = 'Position the barcode within the camera view';
    }

    /**
     * Toggle scanner on/off
     */
    async function toggleScanner() {
        if (showScanner.value) {
            stopScanner();
        } else {
            showScanner.value = true;
            await nextTick();
            const granted = await ensureCameraPermission();
            if (!granted) {
                scanning.value = false;
                scannerStatus.value = 'Camera permission is required to use the scanner.';
                if (onError) {
                    onError(new Error('Camera permission required'));
                }
                return;
            }
            await startScanner();
        }
    }

    /**
     * Switch to a different camera
     * @param {string} cameraId - Device ID of the camera to switch to
     */
    async function switchCamera(cameraId) {
        if (cameraId && cameraId !== selectedCameraId.value) {
            selectedCameraId.value = cameraId;
            if (showScanner.value && codeReader) {
                codeReader.reset();
                await nextTick();
                await startScanner();
            }
        }
    }

    // Watch for camera selection changes
    watch(selectedCameraId, async (newId, oldId) => {
        if (showScanner.value && newId && oldId && newId !== oldId) {
            if (codeReader) {
                codeReader.reset();
            }
            await nextTick();
            await startScanner();
        }
    });

    // Cleanup on unmount
    onUnmounted(() => {
        stopScanner();
    });

    return {
        // Refs
        showScanner,
        scanning,
        scannerStatus,
        videoRef,
        cameras,
        selectedCameraId,
        hasCameraPermission,

        // Methods
        startScanner,
        stopScanner,
        toggleScanner,
        switchCamera,
        ensureCameraPermission,
    };
}
