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

export function useSchoolUserProfileSetup(args: any = {}) {
  const { props, emit } = args;
  return useMobileIdProfileLogic(props ?? {}, emit);
}
