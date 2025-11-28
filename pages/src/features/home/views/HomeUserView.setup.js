import { useHomeUserLogic } from '@home/composables/useHomeUserLogic.js';

// Components
import UserProfile from '@user/components/UserProfile.vue';
import BarcodeDisplay from '@user/components/BarcodeDisplay.vue';
import UserMenu from '@user/components/UserMenu.vue';

// CSS
import '@/assets/styles/home/home-merged.css';

export { UserProfile, BarcodeDisplay, UserMenu };

export function useHomeUserViewSetup() {
  return useHomeUserLogic();
}
