<!-- src/views/Home.vue -->
<template>
  <div
    v-if="loading"
    class="md-loading-container md-flex md-flex-column md-items-center md-justify-center md-theme-dark"
  >
    <md-circular-progress indeterminate></md-circular-progress>
    <p class="md-typescale-body-large md-mt-4">Loading...</p>
  </div>

  <!-- Based on user groups -->
  <HomeSchool v-else-if="groups.includes('School')" />
  <HomeUser v-else-if="groups.includes('User')" />
  <div v-else class="error-page md-flex md-items-center md-justify-center md-p-6">
    <div class="error-content md-card md-rounded-xl md-p-8 md-text-center md-max-w-lg">
      <div class="error-icon-wrapper md-flex md-justify-center md-mb-6">
        <div class="error-icon md-flex md-items-center md-justify-center">
          <md-icon>error</md-icon>
        </div>
      </div>
      <h2 class="md-typescale-headline-medium md-mb-2">
        {{ window.apiError ? 'Connection Error' : 'Access Denied' }}
      </h2>
      <p class="md-typescale-body-large md-mb-6">
        {{ window.apiError || 'Unknown user group. Please contact your administrator.' }}
      </p>
      <div
        v-if="window.apiError"
        class="error-details md-card md-card-filled md-rounded-lg md-p-4 md-mb-6 md-text-left"
      >
        <p class="md-typescale-body-medium md-mb-3">
          Unable to connect to the server. Please check:
        </p>
        <ul class="error-list md-m-0 md-p-0">
          <li class="md-typescale-body-medium">Your internet connection is active</li>
          <li class="md-typescale-body-medium">The server is running and accessible</li>
          <li class="md-typescale-body-medium">Your network allows access to the server</li>
        </ul>
        <p class="error-code md-typescale-label-medium md-mt-4">Error: {{ window.apiError }}</p>
      </div>
      <div
        v-else
        class="error-details md-card md-card-filled md-rounded-lg md-p-4 md-mb-6 md-text-left"
      >
        <p class="md-typescale-body-medium md-mb-3">
          Your account is not assigned to a valid user group.
        </p>
        <ul class="error-list md-m-0 md-p-0">
          <li class="md-typescale-body-medium">Contact your system administrator</li>
          <li class="md-typescale-body-medium">
            Request assignment to either "User" or "School" group
          </li>
        </ul>
      </div>
      <md-filled-button class="retry-button" @click="retryConnection">
        <md-icon slot="icon">refresh</md-icon>
        Retry Connection
      </md-filled-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import HomeSchool from './HomeSchool.vue';
import HomeUser from './HomeUser.vue';
import '@/assets/css/home-merged.css';

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
</script>
