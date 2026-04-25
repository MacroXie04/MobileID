import { useRegisterLogic } from '@auth/composables/useRegisterLogic';
import '@auth/styles/auth.css';

export function useRegisterViewSetup() {
  return useRegisterLogic();
}
