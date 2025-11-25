import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getUserProfile, updateUserProfile } from '@shared/api/auth';
import { baseURL } from '@/config';
import { getAccessToken } from '@shared/api/axios';
import { useImageCropper } from '@user/composables/useImageCropper.js';
import { useAutoSave } from '@shared/composables/useAutoSave.js';
import { fileToBase64, validateImageFile } from '@user/utils/imageUtils.js';
import avatarPlaceholder from '@/assets/images/user/avatar_placeholder.png';

export function useProfileEditLogic() {
  const router = useRouter();

  // Refs
  const fileInput = ref(null);
  const cropperDialog = ref(null);

  // State
  const loading = ref(false);
  const formData = ref({
    name: '',
    information_id: '',
  });
  const avatarFile = ref(null);
  const avatarPreviewUrl = ref('');
  const errors = ref({});
  const successMessage = ref('');
  const originalData = ref({});

  // Image cropper composable (simple version without advanced controls)
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

  // Auto-save changes function
  async function autoSaveChanges() {
    // Prepare data for auto-save
    const profileData = {
      name: formData.value.name,
      information_id: formData.value.information_id,
    };

    // Check if text fields have changed
    const textFieldsChanged = JSON.stringify(profileData) !== JSON.stringify(originalData.value);

    // Add base64 avatar if there's a new one
    if (avatarFile.value) {
      profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
    }

    // Only auto-save if data has actually changed
    if (!textFieldsChanged && !avatarFile.value) {
      return { success: false };
    }

    const response = await updateUserProfile(profileData);

    if (response.success) {
      // Update original data to match current data
      originalData.value = {
        name: formData.value.name,
        information_id: formData.value.information_id,
      };

      // Clear avatar file after successful save
      if (avatarFile.value) {
        avatarFile.value = null;
      }

      return { success: true, message: 'Profile auto-saved successfully' };
    } else {
      return { success: false, message: response.message || 'Auto-save failed' };
    }
  }

  // Auto-save composable
  const {
    autoSaving,
    lastSaved,
    autoSaveStatus,
    triggerAutoSave,
    getStatusText: getAutoSaveStatusText,
  } = useAutoSave(autoSaveChanges, {
    debounceMs: 1500,
  });

  // Methods
  const getAvatarSrc = () => {
    return avatarPreviewUrl.value || avatarPlaceholder;
  };

  const selectImage = () => {
    fileInput.value?.click();
  };

  const clearError = (field) => {
    delete errors.value[field];
    if (field !== 'general') {
      delete errors.value.general;
    }
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file
    const validation = validateImageFile(file, {
      allowedTypes: /^image\/(jpe?g|png)$/i,
      maxSizeMB: 5,
    });

    if (!validation.success) {
      errors.value.user_profile_img = validation.error;
      fileInput.value.value = '';
      return;
    }

    // Clear previous errors
    delete errors.value.user_profile_img;

    // Create temporary URL and initialize cropper
    const tempUrl = URL.createObjectURL(file);
    await initializeCropper(tempUrl);
  };

  const applyCrop = async () => {
    try {
      const result = await applyCropBase();

      if (result) {
        avatarFile.value = result.file;

        // Update preview URL
        if (avatarPreviewUrl.value) {
          URL.revokeObjectURL(avatarPreviewUrl.value);
        }
        avatarPreviewUrl.value = result.previewUrl;

        // Trigger auto-save for avatar change
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

  const handleFieldChange = (field) => {
    clearError(field);
    triggerAutoSave();
  };

  const handleSubmit = async () => {
    if (loading.value) return;

    loading.value = true;
    errors.value = {};

    try {
      // Prepare data including base64 avatar if available
      const profileData = { ...formData.value };

      // Add base64 avatar if there's a new one
      if (avatarFile.value) {
        profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
      }

      // Update profile with avatar data included
      const response = await updateUserProfile(profileData);
      if (!response.success) {
        if (response.errors) {
          Object.keys(response.errors).forEach((key) => {
            if (Array.isArray(response.errors[key])) {
              errors.value[key] = response.errors[key][0];
            } else {
              errors.value[key] = response.errors[key];
            }
          });
        } else {
          errors.value.general = response.message || 'Update failed';
        }
        return;
      }

      // Success - show message then redirect
      successMessage.value = 'Profile updated successfully!';

      // Update original data to match current data
      originalData.value = {
        name: formData.value.name,
        information_id: formData.value.information_id,
      };

      // Clear cached user info to force refresh on home page
      window.userInfo = null;

      setTimeout(() => {
        router.push('/');
      }, 1500);
    } catch (error) {
      console.error('Update error:', error);
      errors.value.general = 'Network error. Please try again.';
    } finally {
      loading.value = false;
    }
  };

  const loadProfile = async () => {
    try {
      const response = await getUserProfile();
      if (response.success) {
        formData.value = { ...response.data };
        // Initialize original data for auto-save comparison
        originalData.value = {
          name: response.data.name || '',
          information_id: response.data.information_id || '',
        };

        // Load avatar separately
        try {
          const token = getAccessToken();
          const headers = token ? { Authorization: `Bearer ${token}` } : {};
          const avatarResponse = await fetch(`${baseURL}/authn/user_img/`, {
            headers,
          });
          if (avatarResponse.ok) {
            const blob = await avatarResponse.blob();
            avatarPreviewUrl.value = URL.createObjectURL(blob);
          }
        } catch (_avatarError) {
          console.log('No avatar found or error loading avatar');
        }
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      errors.value.general = 'Failed to load profile data';
    }
  };

  // Lifecycle
  onMounted(() => {
    loadProfile();
  });

  onUnmounted(() => {
    if (avatarPreviewUrl.value) {
      URL.revokeObjectURL(avatarPreviewUrl.value);
    }
    // Auto-save and cropper cleanup is handled by composables
  });

  return {
    fileInput,
    cropperDialog,
    loading,
    formData,
    errors,
    successMessage,
    cropperImage,
    showCropper,
    autoSaving,
    lastSaved,
    autoSaveStatus,
    getAutoSaveStatusText,
    getAvatarSrc,
    selectImage,
    handleFileSelect,
    applyCrop,
    cancelCrop,
    handleDialogClose,
    handleFieldChange,
    handleSubmit,
    resetCrop,
  };
}
