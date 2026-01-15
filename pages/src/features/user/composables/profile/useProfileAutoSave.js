import { useAutoSave } from '@shared/composables/useAutoSave.js';
import { updateUserProfile } from '@shared/api/auth';
import { fileToBase64 } from '@user/utils/imageUtils.js';

export function useProfileAutoSave({ formData, avatarFile, originalData }) {
  async function autoSaveChanges() {
    const profileData = {
      name: formData.value.name,
      information_id: formData.value.information_id,
    };

    const textFieldsChanged = JSON.stringify(profileData) !== JSON.stringify(originalData.value);

    if (avatarFile.value) {
      profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
    }

    if (!textFieldsChanged && !avatarFile.value) {
      return { skipped: true };
    }

    const response = await updateUserProfile(profileData);

    if (response.success) {
      originalData.value = {
        name: formData.value.name,
        information_id: formData.value.information_id,
      };

      if (avatarFile.value) {
        avatarFile.value = null;
      }

      return { success: true, message: 'Profile auto-saved successfully' };
    }

    return { success: false, message: response.message || 'Auto-save failed' };
  }

  const {
    autoSaving,
    lastSaved,
    autoSaveStatus,
    triggerAutoSave,
    getStatusText: getAutoSaveStatusText,
  } = useAutoSave(autoSaveChanges, {
    debounceMs: 1500,
  });

  return {
    autoSaving,
    lastSaved,
    autoSaveStatus,
    triggerAutoSave,
    getAutoSaveStatusText,
  };
}
