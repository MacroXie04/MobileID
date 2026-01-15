import { onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useRegisterValidation } from '@auth/composables/useRegisterValidation.js';
import { useRegisterAvatar } from '@auth/composables/register/useRegisterAvatar.js';
import { useRegisterSubmit } from '@auth/composables/register/useRegisterSubmit.js';

export function useRegisterLogic() {
  const router = useRouter();

  // State
  const loading = ref(false);
  const formData = ref({
    username: '',
    name: '',
    password1: '',
    password2: '',
    user_profile_img_base64: '',
  });
  const showPassword1 = ref(false);
  const showPassword2 = ref(false);

  // Validation composable
  const {
    errors,
    clearError,
    validateField: validateSingleField,
    validateForm,
    setServerErrors,
    setGeneralError,
  } = useRegisterValidation();

  // Register avatar composable with advanced controls
  const registerAvatar = useRegisterAvatar({ errors, formData });

  // Wrapper function to pass formData to validation
  function validateField(field) {
    validateSingleField(field, formData.value);
  }

  const { handleSubmit } = useRegisterSubmit({
    formData,
    errors,
    loading,
    router,
    validateForm,
    setServerErrors,
    setGeneralError,
  });

  // Cleanup
  onUnmounted(() => {
    registerAvatar.cleanupAvatarPreview();
  });

  return {
    // Refs
    fileInput: registerAvatar.fileInput,
    cropperDialog: registerAvatar.cropperDialog,
    cropperImage: registerAvatar.cropperImage,
    cropperPreview: registerAvatar.cropperPreview,

    // State
    loading,
    formData,
    showPassword1,
    showPassword2,
    errors,

    // Cropper state
    showCropper: registerAvatar.showCropper,
    cropperLoading: registerAvatar.cropperLoading,
    applyingCrop: registerAvatar.applyingCrop,
    zoomLevel: registerAvatar.zoomLevel,

    // Methods
    getAvatarSrc: registerAvatar.getAvatarSrc,
    selectImage: registerAvatar.selectImage,
    handleFileSelect: registerAvatar.handleFileSelect,
    clearError,
    validateField,
    handleSubmit,

    // Cropper methods
    zoomIn: registerAvatar.zoomIn,
    zoomOut: registerAvatar.zoomOut,
    handleZoomChange: registerAvatar.handleZoomChange,
    applyCrop: registerAvatar.applyCrop,
    cancelCrop: registerAvatar.cancelCrop,
    resetCrop: registerAvatar.resetCrop,
    handleDialogClose: registerAvatar.handleDialogClose,
  };
}
