import { onMounted, ref } from 'vue';
import HomeSchoolView from './HomeSchoolView.vue';
import { getUserInfo, getApiError } from '@shared/state/authState';
import '@/assets/styles/home/home-merged.css';

export { HomeSchoolView };

export function useHomeViewSetup() {
  const loading = ref(true);
  const apiError = ref(null);

  onMounted(() => {
    // Check if API error occurred (connection failed)
    const storedError = getApiError();
    if (storedError) {
      apiError.value = storedError;
      loading.value = false;
      return;
    }

    // If user info exists, we're good — show the home view
    const data = getUserInfo();
    if (!data) {
      apiError.value = 'Unable to load user data';
    }

    loading.value = false;
  });

  // Retry connection function
  function retryConnection() {
    window.location.reload();
  }

  return { loading, apiError, retryConnection };
}
