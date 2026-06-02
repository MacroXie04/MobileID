import { useMobileIdProfileLogic } from '@mobile-id/composables/useMobileIdProfileLogic';
import '@mobile-id/styles/mobile-id.css';
import type { PropType } from 'vue';
import type { UserProfile } from '@profile';

export const propsDefinition = {
  profile: {
    type: Object as PropType<UserProfile>,
    required: true,
  },
  avatarSrc: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  barcodeVisible: {
    type: Boolean,
    default: false,
  },
  isRefreshingToken: {
    type: Boolean,
    default: false,
  },
};

export const emitsDefinition = ['generate'];

export interface UserProfileSetupArgs {
  // Fields are optional because Vue's `defineProps(propsDefinition)` infers the
  // bound props with optional/defaulted members; useMobileIdProfileLogic only
  // reads avatarSrc/profile and tolerates their absence at runtime.
  props?: {
    profile?: UserProfile;
    avatarSrc?: string;
    loading?: boolean;
    barcodeVisible?: boolean;
    isRefreshingToken?: boolean;
  };
  emit?: (event: 'generate') => void;
}

export function useSchoolUserProfileSetup(args: UserProfileSetupArgs = {}) {
  const { props, emit } = args;
  return useMobileIdProfileLogic(props ?? {}, emit);
}
