import { useSchoolProfileLogic } from '@school/composables/useSchoolProfileLogic.js';
import '@school/styles/school.css';

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
