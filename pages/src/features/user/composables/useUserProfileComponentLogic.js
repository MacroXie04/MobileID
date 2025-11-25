import { computed, ref, watch, toRefs } from 'vue';
import defaultAvatar from '@/assets/images/user/avatar_placeholder.png';
import { getInitials, handleAvatarError } from '@user/utils/profileUtils.js';

export function useUserProfileComponentLogic(props) {
  const { avatarSrc, profile } = toRefs(props);
  const showInitials = ref(false);

  // Computed
  const avatarUrl = computed(() => {
    if (avatarSrc.value) {
      return avatarSrc.value;
    }
    return null;
  });

  // Watch for avatarSrc changes
  watch(avatarSrc, (newVal) => {
    if (newVal) {
      showInitials.value = false;
    }
  });

  // Handle image loading error
  function handleImageError(event) {
    handleAvatarError(event, {
      profileName: profile.value?.name,
      placeholderSrc: defaultAvatar,
      onShowInitials: () => {
        showInitials.value = true;
      },
    });
  }

  return {
    showInitials,
    avatarUrl,
    getInitials,
    handleImageError,
  };
}
