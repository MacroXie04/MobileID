import { onMounted, ref } from 'vue';
import HomeSchoolView from './HomeSchoolView.vue';
import HomeUserView from './HomeUserView.vue';
import { getUserInfo, getApiError } from '@shared/state/authState';
import '@/assets/styles/home/home-merged.css';

export { HomeSchoolView, HomeUserView };

export function useHomeViewSetup() {
  const loading = ref(true);
  const groups = ref([]);
  const apiError = ref(null);

  onMounted(() => {
    const data = getUserInfo();

    // Check if API error occurred (connection failed)
    const storedError = getApiError();
    if (storedError) {
      apiError.value = storedError;
      groups.value = [];
      loading.value = false;
      return;
    }

    // If data exists, set groups
    if (data) {
      groups.value = data.groups || [];
    } else {
      // No data and no API error means unknown user group
      groups.value = [];
    }

    loading.value = false;
  });

  // Retry connection function
  function retryConnection() {
    window.location.reload();
  }

  return { loading, groups, apiError, retryConnection };
}
