import { onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { register, userInfo } from '@shared/api/auth.js';
import { useRegisterValidation } from '@auth/composables/useRegisterValidation.js';
import { useImageCropper } from '@user/composables/useImageCropper.js';
import { validateImageFile } from '@user/utils/imageUtils.js';

export function useRegisterLogic() {
  const router = useRouter();

  // Refs
  const fileInput = ref(null);
  const cropperDialog = ref(null);

  // State
  const loading = ref(false);
  const formData = ref({
    username: '',
    name: '',
    information_id: '',
    password1: '',
    password2: '',
    user_profile_img_base64: '',
  });
  const avatarFile = ref(null);
  const avatarPreviewUrl = ref('');
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

  // Image cropper composable with advanced controls
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

  // Methods
  const getAvatarSrc = () => {
    return avatarPreviewUrl.value || '/images/avatar_placeholder.png';
  };

  const selectImage = () => {
    fileInput.value?.click();
  };

  // Wrapper function to pass formData to validation
  function validateField(field) {
    validateSingleField(field, formData.value);
  }

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file
    const validation = validateImageFile(file);
    if (!validation.success) {
      errors.user_profile_img = [validation.error];
      fileInput.value.value = '';
      return;
    }

    // Clear previous errors
    delete errors.user_profile_img;

    // Create temporary URL and initialize cropper
    const tempUrl = URL.createObjectURL(file);
    await initializeCropper(tempUrl);
  };

  // Apply crop wrapper
  const applyCrop = async () => {
    try {
      const result = await applyCropBase({ maxBase64Length: 30000 });

      if (result) {
        avatarFile.value = result.file;
        formData.value.user_profile_img_base64 = result.base64;

        // Update preview URL
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

  const handleSubmit = async () => {
    if (loading.value) return;

    // Validate form
    if (!validateForm(formData.value)) {
      return;
    }

    loading.value = true;
    Object.keys(errors).forEach((key) => delete errors[key]);

    try {
      // Register user
      const response = await register(formData.value);

      if (!response.success) {
        // Handle API errors
        if (response.errors) {
          setServerErrors(response.errors);
        } else {
          setGeneralError(
            response.detail ||
              response.message ||
              'Registration failed. Please check your information.'
          );
        }
        return;
      }

      // Success - avatar was already included in registration data as base64
      // Verify session establishment before redirecting
      try {
        const user = await userInfo();
        if (user) {
          window.userInfo = user;
          await router.push('/');
        } else {
          // If session not established (e.g. backend didn't log them in automatically), go to login
          await router.push('/login');
        }
      } catch {
        // Fallback to login if verification fails
        await router.push('/login');
      }
    } catch (error) {
      console.error('Registration error:', error);

      // Try to parse error message for API errors
      try {
        const errorData = JSON.parse(error.message);
        if (errorData.message) {
          setGeneralError(errorData.message);
        } else if (errorData.errors) {
          setServerErrors(errorData.errors);
        } else {
          setGeneralError('Registration failed. Please try again.');
        }
      } catch (_parseError) {
        setGeneralError('Network error. Please check your connection and try again.');
      }
    } finally {
      loading.value = false;
    }
  };

  // Cleanup
  onUnmounted(() => {
    if (avatarPreviewUrl.value) {
      URL.revokeObjectURL(avatarPreviewUrl.value);
    }
    // Cropper cleanup is handled by the composable
  });

  return {
    // Refs
    fileInput,
    cropperDialog,
    cropperImage,
    cropperPreview,

    // State
    loading,
    formData,
    showPassword1,
    showPassword2,
    errors,
    
    // Cropper state
    showCropper,
    cropperLoading,
    applyingCrop,
    zoomLevel,

    // Methods
    getAvatarSrc,
    selectImage,
    handleFileSelect,
    clearError,
    validateField,
    handleSubmit,
    
    // Cropper methods
    zoomIn,
    zoomOut,
    handleZoomChange,
    applyCrop,
    cancelCrop,
    resetCrop,
    handleDialogClose
  };
}

