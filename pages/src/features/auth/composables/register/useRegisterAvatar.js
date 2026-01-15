import { ref } from 'vue';
import { useImageCropper } from '@user/composables/useImageCropper.js';
import { validateImageFile } from '@user/utils/imageUtils.js';
import avatarPlaceholder from '@/assets/images/user/avatar_placeholder.png';

export function useRegisterAvatar({ errors, formData }) {
  const fileInput = ref(null);
  const cropperDialog = ref(null);
  const avatarFile = ref(null);
  const avatarPreviewUrl = ref('');

  const {
    cropperImage,
    cropperPreview,
    showCropper,
    cropperLoading,
    applyingCrop,
    zoomLevel,
    initializeCropper,
    resetCrop,
    zoomIn,
    zoomOut,
    handleZoomChange,
    applyCrop: applyCropBase,
    closeCropper,
  } = useImageCropper({
    targetWidth: 128,
    targetHeight: 128,
    quality: 0.7,
    enableAdvancedControls: true,
  });

  const getAvatarSrc = () => {
    return avatarPreviewUrl.value || avatarPlaceholder;
  };

  const selectImage = () => {
    fileInput.value?.click();
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validation = validateImageFile(file);
    if (!validation.success) {
      errors.user_profile_img = [validation.error];
      fileInput.value.value = '';
      return;
    }

    delete errors.user_profile_img;

    const tempUrl = URL.createObjectURL(file);
    await initializeCropper(tempUrl);
  };

  const applyCrop = async () => {
    try {
      const result = await applyCropBase({ maxBase64Length: 30000 });

      if (result) {
        avatarFile.value = result.file;
        formData.value.user_profile_img_base64 = result.base64;

        if (avatarPreviewUrl.value) {
          URL.revokeObjectURL(avatarPreviewUrl.value);
        }
        avatarPreviewUrl.value = result.previewUrl;
      }

      closeCropper();
      fileInput.value.value = '';
    } catch (error) {
      console.error('Failed to apply crop:', error);
      errors.user_profile_img = ['Failed to process image. Please try again.'];
    }
  };

  const cancelCrop = () => {
    closeCropper();
    fileInput.value.value = '';
  };

  const handleDialogClose = () => {
    closeCropper();
    fileInput.value.value = '';
  };

  const cleanupAvatarPreview = () => {
    if (avatarPreviewUrl.value) {
      URL.revokeObjectURL(avatarPreviewUrl.value);
    }
  };

  return {
    fileInput,
    cropperDialog,
    cropperImage,
    cropperPreview,
    showCropper,
    cropperLoading,
    applyingCrop,
    zoomLevel,
    getAvatarSrc,
    selectImage,
    handleFileSelect,
    applyCrop,
    cancelCrop,
    resetCrop,
    handleDialogClose,
    zoomIn,
    zoomOut,
    handleZoomChange,
    cleanupAvatarPreview,
  };
}
