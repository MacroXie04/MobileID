import { computed, ref, toRefs } from 'vue';
import { getInitials } from '@shared/utils/profileUtils';
import type { UserProfile } from '@profile';

export function useMobileIdProfileLogic(
  props: { avatarSrc: string; profile: UserProfile },
  emit: (event: 'generate') => void
) {
  const { avatarSrc } = toRefs(props);
  const showInitials = ref(false);

  const shouldShowAvatar = computed(() => {
    return avatarSrc.value && !showInitials.value;
  });

  function handleImageError() {
    showInitials.value = true;
  }

  function handleGenerate() {
    emit('generate');
  }

  return {
    showInitials,
    shouldShowAvatar,
    getInitials,
    handleImageError,
    handleGenerate,
  };
}
