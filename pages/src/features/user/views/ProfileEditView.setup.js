import { useRouter } from 'vue-router';
import { useProfileEditLogic } from '@user/composables/useProfileEditLogic.js';
import '@/assets/styles/auth/auth-merged.css';

export function useProfileEditViewSetup() {
  const router = useRouter();
  return {
    router,
    ...useProfileEditLogic(),
  };
}
