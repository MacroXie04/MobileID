import { nextTick, onUnmounted, ref } from 'vue';
import Cropper from 'cropperjs';
import 'cropperjs/dist/cropper.css';

/**
 * Composable for handling image cropping functionality
 * @param {Object} options - Configuration options
 * @param {number} options.targetWidth - Target width for cropped image (default: 128)
 * @param {number} options.targetHeight - Target height for cropped image (default: 128)
 * @param {number} options.quality - JPEG quality 0-1 (default: 0.7)
 * @param {boolean} options.enableAdvancedControls - Enable zoom controls and preview (default: false)
 * @returns {Object} Cropper functions and state
 */
export function useImageCropper(options = {}) {
  const {
    targetWidth = 128,
    targetHeight = 128,
    quality = 0.7,
    enableAdvancedControls = false,
  } = options;

  // Refs
  const cropperImage = ref(null);
  const cropperPreview = ref(null);
  const cropper = ref(null);
  const showCropper = ref(false);
  const tempImageUrl = ref('');
  const cropperLoading = ref(false);
  const applyingCrop = ref(false);
  const zoomLevel = ref(1);

  /**
   * Initialize cropper with an image URL
   * @param {string} imageUrl - URL of the image to crop
   */
  async function initializeCropper(imageUrl) {
    showCropper.value = true;
    cropperLoading.value = true;
    tempImageUrl.value = imageUrl;

    await nextTick();

    if (!cropperImage.value || !tempImageUrl.value) return;

    // Destroy previous cropper instance
    if (cropper.value) {
      cropper.value.destroy();
      cropper.value = null;
    }

    // Load image and initialize cropper
    cropperImage.value.onload = () => {
      try {
        const isMobile = window.innerWidth <= 640;

        cropper.value = new Cropper(cropperImage.value, {
          aspectRatio: 1,
          viewMode: 2,
          dragMode: 'move',
          autoCropArea: isMobile ? 0.9 : 0.8,
          restore: false,
          guides: !isMobile,
          center: true,
          highlight: false,
          cropBoxMovable: true,
          cropBoxResizable: true,
          toggleDragModeOnDblclick: !isMobile,
          minContainerWidth: isMobile ? 280 : 300,
          minContainerHeight: isMobile ? 280 : 300,
          minCropBoxWidth: isMobile ? 80 : 100,
          minCropBoxHeight: isMobile ? 80 : 100,
          responsive: true,
          checkOrientation: false,
          modal: true,
          background: true,
          scalable: true,
          zoomable: true,
          wheelZoomRatio: isMobile ? 0.05 : 0.1,
          ready() {
            if (enableAdvancedControls) {
              updatePreview();
            }
            cropperLoading.value = false;
          },
          crop: enableAdvancedControls ? updatePreview : null,
        });

        zoomLevel.value = 1;
      } catch (error) {
        console.error('Failed to initialize cropper:', error);
        cropperLoading.value = false;
      }
    };

    cropperImage.value.onerror = () => {
      console.error('Failed to load image');
      cropperLoading.value = false;
    };

    cropperImage.value.src = tempImageUrl.value;
  }

  /**
   * Update preview (for advanced mode with preview panel)
   */
  function updatePreview() {
    if (!cropper.value || !cropperPreview.value) return;

    try {
      const canvas = cropper.value.getCroppedCanvas({
        width: targetWidth,
        height: targetHeight,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
      });

      cropperPreview.value.innerHTML = '';

      const previewImg = document.createElement('img');
      previewImg.src = canvas.toDataURL();
      previewImg.style.width = '100%';
      previewImg.style.height = '100%';
      previewImg.style.objectFit = 'cover';
      previewImg.style.borderRadius = '50%';

      cropperPreview.value.appendChild(previewImg);
    } catch (error) {
      console.error('Failed to update preview:', error);
    }
  }

  /**
   * Reset crop to original state
   */
  function resetCrop() {
    if (cropper.value) {
      cropper.value.reset();
      cropper.value.setDragMode('move');
      zoomLevel.value = 1;
      if (enableAdvancedControls) {
        updatePreview();
      }
    }
  }

  /**
   * Zoom in on the image
   */
  function zoomIn() {
    if (cropper.value && zoomLevel.value < 3) {
      zoomLevel.value = Math.min(3, zoomLevel.value + 0.2);
      cropper.value.zoomTo(zoomLevel.value);
    }
  }

  /**
   * Zoom out on the image
   */
  function zoomOut() {
    if (cropper.value && zoomLevel.value > 0.1) {
      zoomLevel.value = Math.max(0.1, zoomLevel.value - 0.2);
      cropper.value.zoomTo(zoomLevel.value);
    }
  }

  /**
   * Handle zoom level changes from slider
   */
  function handleZoomChange() {
    if (cropper.value) {
      cropper.value.zoomTo(parseFloat(zoomLevel.value));
    }
  }

  /**
   * Apply crop and get result
   * @param {Object} options - Apply options
   * @param {number} options.maxBase64Length - Maximum base64 length (default: 30000)
   * @returns {Promise<Object>} Result containing file, blob, and base64
   */
  async function applyCrop({ maxBase64Length = 30000 } = {}) {
    if (!cropper.value || applyingCrop.value) return null;

    applyingCrop.value = true;

    try {
      let canvas = cropper.value.getCroppedCanvas({
        width: targetWidth,
        height: targetHeight,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'medium',
      });

      // Convert to blob
      const blob = await new Promise((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', quality);
      });

      if (!blob) throw new Error('Failed to create blob from canvas');

      // Create file from blob
      const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });

      // Convert to base64
      let base64String = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          resolve(reader.result.split(',')[1]);
        };
        reader.readAsDataURL(blob);
      });

      // If base64 is too large, compress further
      if (base64String.length > maxBase64Length) {
        console.warn('Image too large, reducing quality further...');

        const smallerCanvas = cropper.value.getCroppedCanvas({
          width: Math.floor(targetWidth * 0.75),
          height: Math.floor(targetHeight * 0.75),
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'low',
        });

        const smallerBlob = await new Promise((resolve) => {
          smallerCanvas.toBlob(resolve, 'image/jpeg', quality * 0.7);
        });

        base64String = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            resolve(reader.result.split(',')[1]);
          };
          reader.readAsDataURL(smallerBlob);
        });

        if (base64String.length > maxBase64Length) {
          throw new Error('Image is too large even after compression. Please try a smaller image.');
        }

        return {
          file: new File([smallerBlob], 'avatar.jpg', { type: 'image/jpeg' }),
          blob: smallerBlob,
          base64: base64String,
          previewUrl: URL.createObjectURL(smallerBlob),
        };
      }

      return {
        file,
        blob,
        base64: base64String,
        previewUrl: URL.createObjectURL(blob),
      };
    } catch (error) {
      console.error('Failed to apply crop:', error);
      throw error;
    } finally {
      applyingCrop.value = false;
    }
  }

  /**
   * Close and cleanup cropper
   */
  function closeCropper() {
    showCropper.value = false;

    if (cropper.value) {
      cropper.value.destroy();
      cropper.value = null;
    }

    if (tempImageUrl.value) {
      URL.revokeObjectURL(tempImageUrl.value);
      tempImageUrl.value = '';
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    if (cropper.value) {
      cropper.value.destroy();
    }
    if (tempImageUrl.value) {
      URL.revokeObjectURL(tempImageUrl.value);
    }
  });

  return {
    // Refs
    cropperImage,
    cropperPreview,
    showCropper,
    cropperLoading,
    applyingCrop,
    zoomLevel,

    // Methods
    initializeCropper,
    updatePreview,
    resetCrop,
    zoomIn,
    zoomOut,
    handleZoomChange,
    applyCrop,
    closeCropper,
  };
}
