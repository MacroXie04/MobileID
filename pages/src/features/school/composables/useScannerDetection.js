import { nextTick, onUnmounted, ref, watch } from 'vue';

/**
 * Composable for scanner detection using TensorFlow.js COCO-SSD model
 * Detects objects that might indicate a barcode scanner is present
 * @param {Object} options - Configuration options
 * @param {Function} options.onDetected - Callback when scanner is detected
 * @param {Function} options.onError - Callback when error occurs
 * @param {Boolean} options.preferFrontCamera - Whether to prefer front camera (default: true)
 * @param {Ref} options.videoRef - External video element ref (optional)
 * @param {Ref} options.canvasRef - External canvas element ref (optional)
 * @returns {Object} Detection functions and state
 */
export function useScannerDetection(options = {}) {
  const {
    onDetected,
    onError,
    preferFrontCamera = true,
    videoRef: externalVideoRef,
    canvasRef: externalCanvasRef,
  } = options;

  // State
  const isDetectionActive = ref(false);
  const isModelLoading = ref(false);
  const isModelLoaded = ref(false);
  const detectionStatus = ref('Ready to start detection');
  const videoRef = externalVideoRef || ref(null);
  const canvasRef = externalCanvasRef || ref(null);
  const cameras = ref([]);
  const selectedCameraId = ref(null);
  const hasCameraPermission = ref(false);
  const detectedObjects = ref([]);
  const lastDetectionTime = ref(null);

  // Internal state
  let model = null;
  let stream = null;
  let animationFrameId = null;
  let detectionCooldown = false;

  // Detection configuration
  const DETECTION_COOLDOWN_MS = 2000; // Cooldown between detections to prevent spam
  const CONFIDENCE_THRESHOLD = 0.5; // Minimum confidence for detection

  // Objects that might indicate a scanner is present
  // COCO-SSD can detect: person, cell phone, remote, etc.
  const SCANNER_RELATED_OBJECTS = ['cell phone', 'remote', 'mouse', 'keyboard'];

  /**
   * Check if camera permission was already granted
   */
  async function checkExistingPermission() {
    try {
      // Use Permissions API to check camera status
      if (navigator.permissions && navigator.permissions.query) {
        const result = await navigator.permissions.query({ name: 'camera' });
        if (result.state === 'granted') {
          hasCameraPermission.value = true;
          return true;
        }
      }
    } catch (_err) {
      // Permissions API may not be supported, that's ok
      console.log('Permissions API not supported, will check on request');
    }
    return false;
  }

  // Check permission on init
  checkExistingPermission();

  /**
   * Load the COCO-SSD model
   */
  async function loadModel() {
    if (model || isModelLoading.value) return;

    try {
      isModelLoading.value = true;
      detectionStatus.value = 'Loading AI model...';

      // Dynamically import TensorFlow.js and COCO-SSD
      const [tf, cocoSsd] = await Promise.all([
        import('@tensorflow/tfjs'),
        import('@tensorflow-models/coco-ssd'),
      ]);

      // Set backend to webgl for better performance
      await tf.setBackend('webgl');
      await tf.ready();

      // Load the model
      model = await cocoSsd.load({
        base: 'lite_mobilenet_v2', // Lighter model for mobile devices
      });

      isModelLoaded.value = true;
      detectionStatus.value = 'AI model loaded';
      console.log('COCO-SSD model loaded successfully');
    } catch (error) {
      console.error('Failed to load COCO-SSD model:', error);
      detectionStatus.value = 'Failed to load AI model';
      if (onError) {
        onError(error);
      }
    } finally {
      isModelLoading.value = false;
    }
  }

  /**
   * Check and request camera permission
   * @returns {Promise<boolean>} True if permission granted
   */
  async function ensureCameraPermission() {
    try {
      if (!navigator?.mediaDevices?.getUserMedia) {
        detectionStatus.value = 'Camera is not supported in this browser';
        return false;
      }

      // Request camera access with preference for front camera on mobile
      const constraints = {
        video: {
          facingMode: preferFrontCamera ? 'user' : 'environment',
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
      };

      stream = await navigator.mediaDevices.getUserMedia(constraints);
      hasCameraPermission.value = true;
      return true;
    } catch (err) {
      console.error('Camera permission error:', err);
      hasCameraPermission.value = false;
      detectionStatus.value = 'Camera permission denied';
      return false;
    }
  }

  /**
   * Get available cameras and select the appropriate one
   */
  async function setupCameras() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter((d) => d.kind === 'videoinput');
      cameras.value = videoDevices;

      if (videoDevices.length === 0) {
        detectionStatus.value = 'No cameras found';
        return false;
      }

      // Try to find front camera if preferred
      if (preferFrontCamera) {
        const frontCamera = videoDevices.find(
          (d) =>
            d.label.toLowerCase().includes('front') ||
            d.label.toLowerCase().includes('user') ||
            d.label.toLowerCase().includes('facetime')
        );
        if (frontCamera) {
          selectedCameraId.value = frontCamera.deviceId;
        } else {
          // Fall back to first camera
          selectedCameraId.value = videoDevices[0].deviceId;
        }
      } else {
        // Use environment camera or first available
        const backCamera = videoDevices.find(
          (d) =>
            d.label.toLowerCase().includes('back') ||
            d.label.toLowerCase().includes('environment')
        );
        selectedCameraId.value = backCamera?.deviceId || videoDevices[0].deviceId;
      }

      return true;
    } catch (error) {
      console.error('Failed to enumerate cameras:', error);
      return false;
    }
  }

  /**
   * Start the camera stream
   */
  async function startCamera() {
    try {
      // Stop any existing stream
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }

      const constraints = {
        video: selectedCameraId.value
          ? { deviceId: { exact: selectedCameraId.value } }
          : { facingMode: preferFrontCamera ? 'user' : 'environment' },
      };

      stream = await navigator.mediaDevices.getUserMedia(constraints);

      if (videoRef.value) {
        videoRef.value.srcObject = stream;
        await videoRef.value.play();
      }

      return true;
    } catch (error) {
      console.error('Failed to start camera:', error);
      detectionStatus.value = 'Failed to start camera';
      return false;
    }
  }

  /**
   * Run object detection on current video frame
   */
  async function detectFrame() {
    if (!model || !videoRef.value || !isDetectionActive.value) return;

    try {
      const video = videoRef.value;

      // Skip if video not ready
      if (video.readyState !== 4) {
        animationFrameId = requestAnimationFrame(detectFrame);
        return;
      }

      // Run detection
      const predictions = await model.detect(video);

      // Filter relevant objects
      const relevantObjects = predictions.filter(
        (p) => p.score >= CONFIDENCE_THRESHOLD && SCANNER_RELATED_OBJECTS.includes(p.class)
      );

      detectedObjects.value = relevantObjects;

      // Draw detection boxes on canvas if available
      if (canvasRef.value && relevantObjects.length > 0) {
        drawDetections(relevantObjects);
      }

      // Trigger callback if scanner-related object detected and not in cooldown
      if (relevantObjects.length > 0 && !detectionCooldown) {
        detectionCooldown = true;
        lastDetectionTime.value = Date.now();
        detectionStatus.value = `Detected: ${relevantObjects.map((o) => o.class).join(', ')}`;

        if (onDetected) {
          onDetected(relevantObjects);
        }

        // Reset cooldown after delay
        setTimeout(() => {
          detectionCooldown = false;
        }, DETECTION_COOLDOWN_MS);
      }

      // Continue detection loop
      if (isDetectionActive.value) {
        animationFrameId = requestAnimationFrame(detectFrame);
      }
    } catch (error) {
      console.error('Detection error:', error);
      // Continue trying
      if (isDetectionActive.value) {
        animationFrameId = requestAnimationFrame(detectFrame);
      }
    }
  }

  /**
   * Draw detection boxes on canvas
   */
  function drawDetections(detections) {
    const canvas = canvasRef.value;
    const video = videoRef.value;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((detection) => {
      const [x, y, width, height] = detection.bbox;

      // Draw bounding box
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, width, height);

      // Draw label
      ctx.fillStyle = '#00ff00';
      ctx.font = '16px sans-serif';
      ctx.fillText(`${detection.class} (${Math.round(detection.score * 100)}%)`, x, y - 5);
    });
  }

  /**
   * Start scanner detection
   */
  async function startDetection() {
    try {
      detectionStatus.value = 'Starting detection...';

      // Load model if not already loaded
      if (!model) {
        await loadModel();
      }

      if (!model) {
        detectionStatus.value = 'Failed to load model';
        return false;
      }

      // Request camera permission
      const hasPermission = await ensureCameraPermission();
      if (!hasPermission) {
        if (onError) {
          onError(new Error('Camera permission denied'));
        }
        return false;
      }

      // Setup cameras
      await setupCameras();

      // Start camera
      const cameraStarted = await startCamera();
      if (!cameraStarted) {
        if (onError) {
          onError(new Error('Failed to start camera'));
        }
        return false;
      }

      // Wait for video to be ready
      await nextTick();

      isDetectionActive.value = true;
      detectionStatus.value = 'Scanning for scanner...';

      // Start detection loop
      detectFrame();

      return true;
    } catch (error) {
      console.error('Failed to start detection:', error);
      detectionStatus.value = 'Failed to start detection';
      if (onError) {
        onError(error);
      }
      return false;
    }
  }

  /**
   * Stop scanner detection
   */
  function stopDetection() {
    isDetectionActive.value = false;

    // Stop animation frame
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }

    // Stop camera stream
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }

    // Clear video source
    if (videoRef.value) {
      videoRef.value.srcObject = null;
    }

    detectedObjects.value = [];
    detectionStatus.value = 'Detection stopped';
  }

  /**
   * Toggle detection on/off
   */
  async function toggleDetection() {
    if (isDetectionActive.value) {
      stopDetection();
    } else {
      await startDetection();
    }
  }

  /**
   * Switch to a different camera
   * @param {string} cameraId - Device ID of the camera to switch to
   */
  async function switchCamera(cameraId) {
    if (cameraId && cameraId !== selectedCameraId.value) {
      selectedCameraId.value = cameraId;
      if (isDetectionActive.value) {
        await startCamera();
      }
    }
  }

  // Watch for camera selection changes
  watch(selectedCameraId, async (newId, oldId) => {
    if (isDetectionActive.value && newId && oldId && newId !== oldId) {
      await startCamera();
    }
  });

  // Cleanup on unmount
  onUnmounted(() => {
    stopDetection();
    model = null;
  });

  return {
    // Refs
    isDetectionActive,
    isModelLoading,
    isModelLoaded,
    detectionStatus,
    videoRef,
    canvasRef,
    cameras,
    selectedCameraId,
    hasCameraPermission,
    detectedObjects,
    lastDetectionTime,

    // Methods
    loadModel,
    startDetection,
    stopDetection,
    toggleDetection,
    switchCamera,
    ensureCameraPermission,
  };
}

