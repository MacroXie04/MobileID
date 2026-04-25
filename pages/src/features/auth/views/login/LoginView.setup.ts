import { useLoginLogic } from '@auth/composables/login/useLoginLogic';
import '@auth/styles/auth.css';

export function useLoginViewSetup() {
  return useLoginLogic();
}
