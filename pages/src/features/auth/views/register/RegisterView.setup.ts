import { useRegisterLogic } from '@auth/composables/register/useRegisterLogic';
import '@auth/styles/auth.css';

export function useRegisterViewSetup() {
  return useRegisterLogic();
}
