import { updateUserProfile } from '@shared/api/auth';
import { fileToBase64 } from '@user/utils/imageUtils.js';

export function useProfileSubmit({
  formData,
  avatarFile,
  errors,
  successMessage,
  originalData,
  loading,
  router,
  redirectOnSubmit,
  redirectPath,
}) {
  const handleSubmit = async () => {
    if (loading.value) return;

    loading.value = true;
    errors.value = {};

    try {
      const profileData = { ...formData.value };

      if (avatarFile.value) {
        profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
      }

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

      successMessage.value = 'Profile updated successfully!';

      originalData.value = {
        name: formData.value.name,
        information_id: formData.value.information_id,
      };

      window.userInfo = null;

      if (redirectOnSubmit) {
        setTimeout(() => {
          router.push(redirectPath);
        }, 1500);
      } else {
        setTimeout(() => {
          successMessage.value = '';
        }, 3000);
      }
    } catch (error) {
      console.error('Update error:', error);
      errors.value.general = 'Network error. Please try again.';
    } finally {
      loading.value = false;
    }
  };

  return { handleSubmit };
}
