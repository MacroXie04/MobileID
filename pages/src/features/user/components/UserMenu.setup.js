import { useRouter } from 'vue-router';

// Material Web Components
import '@material/web/icon/icon.js';
import '@material/web/list/list.js';
import '@material/web/list/list-item.js';
import '@material/web/divider/divider.js';

// CSS
import '@/assets/styles/user/user-merged.css';

export const emitsDefinition = ['logout'];

export function useUserMenuSetup({ emit } = {}) {
  const router = useRouter();
  const emitFn = emit ?? (() => {});

  function handleEditProfile() {
    router.push('/profile/edit');
  }

  function handleLogout() {
    emitFn('logout');
  }

  return { handleEditProfile, handleLogout };
}
