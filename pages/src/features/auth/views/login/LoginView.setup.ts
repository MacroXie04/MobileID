import { useLoginLogic } from '@auth/composables/useLoginLogic';
import '@auth/styles/auth.css';

export function useLoginViewSetup() {
  return useLoginLogic();
}
