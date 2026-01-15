import { useLoginLogic } from '@auth/composables/useLoginLogic.js';
import { usePasskeyLogin } from '@auth/composables/usePasskeyLogin.js';
import '@/assets/styles/auth/auth-merged.css';

export function useLoginViewSetup() {
  const loginLogic = useLoginLogic();
  const passkeyLogic = usePasskeyLogin();

  return {
    ...loginLogic,
    ...passkeyLogic,
  };
}
