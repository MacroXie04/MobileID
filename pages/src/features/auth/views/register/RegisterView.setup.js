import { useRegisterLogic } from '@auth/composables/useRegisterLogic.js';
import '@/assets/styles/auth/auth-merged.css';

export function useRegisterViewSetup() {
  return useRegisterLogic();
}
