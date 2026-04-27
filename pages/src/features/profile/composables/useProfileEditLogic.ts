import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useProfileAutoSave } from '@profile/composables/profile/useProfileAutoSave';
import { useProfileAvatar } from '@profile/composables/profile/useProfileAvatar';
import { useProfileLoad } from '@profile/composables/profile/useProfileLoad';
import { useProfileSubmit } from '@profile/composables/profile/useProfileSubmit';

export function useProfileEditLogic(options: any = {}) {
  const { redirectOnSubmit = true, redirectPath = '/' } = options;
  const router = useRouter();

  // State
  const loading = ref(false);
  const formData = ref<Record<string, any>>({
    name: '',
    information_id: '',
  });
  const avatarFile = ref<File | null>(null);
  const avatarPreviewUrl = ref('');
  const errors = ref<Record<string, any>>({});
  const successMessage = ref('');
  const originalData = ref<Record<string, any>>({});

  const { autoSaving, lastSaved, autoSaveStatus, triggerAutoSave, getAutoSaveStatusText } =
    useProfileAutoSave({ formData, avatarFile, originalData });

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

  const clearError = (field: string) => {
    delete errors.value[field];
    if (field !== 'general') {
      delete errors.value.general;
    }
  };

  const handleFieldChange = (field: string) => {
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
