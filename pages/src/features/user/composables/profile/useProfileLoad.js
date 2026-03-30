import { getUserProfile } from '@shared/api/auth';
import { baseURL } from '@app/config/config';

export function useProfileLoad({ formData, originalData, avatarPreviewUrl, errors }) {
  const loadProfile = async () => {
    try {
      const response = await getUserProfile();
      if (response.success) {
        formData.value = { ...response.data };
        originalData.value = {
          name: response.data.name || '',
          information_id: response.data.information_id || '',
        };

        try {
          const avatarResponse = await fetch(`${baseURL}/authn/user_img/`, {
            credentials: 'include',
          });
          if (avatarResponse.ok) {
            const blob = await avatarResponse.blob();
            // Revoke previous blob URL to prevent memory leak
            if (avatarPreviewUrl.value) {
              URL.revokeObjectURL(avatarPreviewUrl.value);
            }
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

  return { loadProfile };
}
