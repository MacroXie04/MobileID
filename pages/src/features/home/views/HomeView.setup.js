import { onMounted, ref } from 'vue';
import HomeSchoolView from './HomeSchoolView.vue';
import HomeUserView from './HomeUserView.vue';
import '@/assets/styles/home/home-merged.css';

export { HomeSchoolView, HomeUserView };

export function useHomeViewSetup() {
  const loading = ref(true);
  const groups = ref([]);

  onMounted(() => {
    // read user info from window.userInfo
    const data = window.userInfo;

    // Check if API error occurred (connection failed)
    if (window.apiError) {
      // API connection failed, show error page
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

  return { loading, groups, retryConnection };
}
