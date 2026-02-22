import { useLoginLogic } from '@auth/composables/useLoginLogic.js';
import '@/assets/styles/auth/auth-merged.css';

export function useLoginViewSetup() {
  return useLoginLogic();
}
