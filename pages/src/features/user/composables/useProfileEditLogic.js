import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useProfileAutoSave } from '@user/composables/profile/useProfileAutoSave.js';
import { useProfileAvatar } from '@user/composables/profile/useProfileAvatar.js';
import { useProfileLoad } from '@user/composables/profile/useProfileLoad.js';
import { useProfileSubmit } from '@user/composables/profile/useProfileSubmit.js';

export function useProfileEditLogic(options = {}) {
  const { redirectOnSubmit = true, redirectPath = '/' } = options;
  const router = useRouter();

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

  const {
    autoSaving,
    lastSaved,
    autoSaveStatus,
    triggerAutoSave,
    getAutoSaveStatusText,
  } = useProfileAutoSave({ formData, avatarFile, originalData });

  const profileAvatar = useProfileAvatar({
    errors,
    avatarFile,
    avatarPreviewUrl,
    triggerAutoSave,
  });

  const { loadProfile } = useProfileLoad({
    formData,
    originalData,
    avatarPreviewUrl,
    errors,
  });

  const { handleSubmit } = useProfileSubmit({
    formData,
    avatarFile,
    errors,
    successMessage,
    originalData,
    loading,
    router,
    redirectOnSubmit,
    redirectPath,
  });

  const clearError = (field) => {
    delete errors.value[field];
    if (field !== 'general') {
      delete errors.value.general;
    }
  };

  const handleFieldChange = (field) => {
    clearError(field);

    // Avoid scheduling auto-save if we haven't loaded baseline data yet, or if the value matches baseline.
    const baseline = originalData.value || {};
    if (!(field in baseline)) return;
    if (formData.value[field] === baseline[field]) return;

    triggerAutoSave();
  };

  // Lifecycle
  onMounted(() => {
    loadProfile();
  });

  onUnmounted(() => {
    profileAvatar.cleanupAvatarPreview();
  });

  return {
    fileInput: profileAvatar.fileInput,
    cropperDialog: profileAvatar.cropperDialog,
    loading,
    formData,
    errors,
    successMessage,
    cropperImage: profileAvatar.cropperImage,
    showCropper: profileAvatar.showCropper,
    autoSaving,
    lastSaved,
    autoSaveStatus,
    getAutoSaveStatusText,
    getAvatarSrc: profileAvatar.getAvatarSrc,
    selectImage: profileAvatar.selectImage,
    handleFileSelect: profileAvatar.handleFileSelect,
    applyCrop: profileAvatar.applyCrop,
    cancelCrop: profileAvatar.cancelCrop,
    handleDialogClose: profileAvatar.handleDialogClose,
    handleFieldChange,
    handleSubmit,
    resetCrop: profileAvatar.resetCrop,
  };
}
