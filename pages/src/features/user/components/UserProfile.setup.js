import { useUserProfileComponentLogic } from '@user/composables/useUserProfileComponentLogic.js';

// CSS
import '@/assets/styles/user/user-merged.css';

export const propsDefinition = {
  profile: {
    type: Object,
    default: () => ({}),
  },
  avatarSrc: {
    type: String,
    default: '',
  },
};

export function useUserProfileSetup({ props } = {}) {
  return useUserProfileComponentLogic(props ?? {});
}
