import { ref } from 'vue';
import { useImageCropper } from '@user/composables/useImageCropper.js';
import { validateImageFile } from '@user/utils/imageUtils.js';
import avatarPlaceholder from '@/assets/images/user/avatar_placeholder.png';

export function useProfileAvatar({
  errors,
  avatarFile,
  avatarPreviewUrl,
  triggerAutoSave,
}) {
  const fileInput = ref(null);
  const cropperDialog = ref(null);

  const {
    cropperImage,
    showCropper,
    initializeCropper,
    resetCrop,
    applyCrop: applyCropBase,
    closeCropper,
  } = useImageCropper({
    targetWidth: 256,
    targetHeight: 256,
    quality: 0.9,
    enableAdvancedControls: false,
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

    const validation = validateImageFile(file, {
      allowedTypes: /^image\/(jpe?g|png)$/i,
      maxSizeMB: 5,
    });

    if (!validation.success) {
      errors.value.user_profile_img = validation.error;
      fileInput.value.value = '';
      return;
    }

    delete errors.value.user_profile_img;

    const tempUrl = URL.createObjectURL(file);
    await initializeCropper(tempUrl);
  };

  const applyCrop = async () => {
    try {
      const result = await applyCropBase();

      if (result) {
        avatarFile.value = result.file;

        if (avatarPreviewUrl.value) {
          URL.revokeObjectURL(avatarPreviewUrl.value);
        }
        avatarPreviewUrl.value = result.previewUrl;

        triggerAutoSave();
      }

      closeCropper();
      fileInput.value.value = '';
    } catch (error) {
      console.error('Failed to apply crop:', error);
      errors.value.user_profile_img = 'Failed to process image. Please try again.';
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
    showCropper,
    getAvatarSrc,
    selectImage,
    handleFileSelect,
    applyCrop,
    cancelCrop,
    handleDialogClose,
    resetCrop,
    cleanupAvatarPreview,
  };
}
