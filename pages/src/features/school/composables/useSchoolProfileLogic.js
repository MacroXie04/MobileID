import { computed, ref, toRefs } from 'vue';
import { getInitials } from '@shared/utils/profileUtils.js';

export function useSchoolProfileLogic(props, emit) {
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
