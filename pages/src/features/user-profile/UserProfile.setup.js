import { useSchoolProfileLogic } from '@/features/useSchoolProfileLogic.js';
import '@/assets/styles/school/school-merged.css';

export const propsDefinition = {
  profile: {
    type: Object,
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

export function useSchoolUserProfileSetup({ props, emit } = {}) {
  return useSchoolProfileLogic(props ?? {}, emit);
}
