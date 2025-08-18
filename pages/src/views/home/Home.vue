<!-- src/views/Home.vue -->
<template>
  <div v-if="loading" class="md-loading-container md-flex md-flex-column md-items-center md-justify-center md-theme-dark">
    <md-circular-progress indeterminate></md-circular-progress>
    <p class="md-typescale-body-large md-mt-4">Loading...</p>
  </div>

  <!-- Based on user groups -->
  <HomeSchool v-else-if="groups.includes('School')"/>
  <HomeUser v-else-if="groups.includes('User')"/>
  <div v-else class="error-page md-flex md-items-center md-justify-center md-p-6">
    <div class="error-content md-card md-rounded-xl md-p-8 md-text-center md-max-w-lg">
      <div class="error-icon-wrapper md-flex md-justify-center md-mb-6">
        <div class="error-icon md-flex md-items-center md-justify-center">
          <md-icon>error</md-icon>
        </div>
      </div>
      <h2 class="md-typescale-headline-medium md-mb-2">{{ window.apiError ? 'Connection Error' : 'Access Denied' }}</h2>
      <p class="md-typescale-body-large md-mb-6">{{ window.apiError || 'Unknown user group. Please contact your administrator.' }}</p>
      <div v-if="window.apiError" class="error-details md-card md-card-filled md-rounded-lg md-p-4 md-mb-6 md-text-left">
        <p class="md-typescale-body-medium md-mb-3">Unable to connect to the server. Please check:</p>
        <ul class="error-list md-m-0 md-p-0">
          <li class="md-typescale-body-medium">Your internet connection is active</li>
          <li class="md-typescale-body-medium">The server is running and accessible</li>
          <li class="md-typescale-body-medium">Your network allows access to the server</li>
        </ul>
        <p class="error-code md-typescale-label-medium md-mt-4">Error: {{ window.apiError }}</p>
      </div>
      <div v-else class="error-details md-card md-card-filled md-rounded-lg md-p-4 md-mb-6 md-text-left">
        <p class="md-typescale-body-medium md-mb-3">Your account is not assigned to a valid user group.</p>
        <ul class="error-list md-m-0 md-p-0">
          <li class="md-typescale-body-medium">Contact your system administrator</li>
          <li class="md-typescale-body-medium">Request assignment to either "User" or "School" group</li>
        </ul>
      </div>
      <md-filled-button @click="retryConnection" class="retry-button">
        <md-icon slot="icon">refresh</md-icon>
        Retry Connection
      </md-filled-button>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref} from "vue";
import HomeSchool from "./HomeSchool.vue";
import HomeUser from "./HomeUser.vue";

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

<style scoped>
/* Page-specific styles for Home.vue - minimal overrides only */

/* Loading container height */
.md-loading-container {
  min-height: 100vh;
}

/* Error page specific styles */
.error-page {
  min-height: 100vh;
  background: var(--md-sys-color-surface-container-lowest);
}

.error-content {
  width: 100%;
}

/* Error icon wrapper */
.error-icon {
  width: 64px;
  height: 64px;
  background: var(--md-sys-color-error-container);
  border-radius: 50%;
  position: relative;
  animation: pulse 2s ease-in-out infinite;
}

.error-icon::before {
  content: '';
  position: absolute;
  inset: -10px;
  background: var(--md-sys-color-error-container);
  border-radius: 50%;
  opacity: 0.3;
  animation: pulse-ring 2s ease-in-out infinite;
}

.error-icon md-icon {
  font-size: 36px;
  color: var(--md-sys-color-on-error-container);
  position: relative;
  z-index: 1;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes pulse-ring {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.1;
  }
}

/* Error list styling */
.error-list {
  list-style: none;
}

.error-list li {
  margin-bottom: var(--md-sys-spacing-2);
  line-height: 1.5;
  position: relative;
  padding-left: var(--md-sys-spacing-6);
}

.error-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--md-sys-color-primary);
  font-weight: bold;
  font-size: 1.2rem;
}

/* Error code styling */
.error-code {
  padding: var(--md-sys-spacing-2) var(--md-sys-spacing-4);
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: var(--md-sys-shape-corner-small);
  font-family: 'Roboto Mono', monospace;
  display: inline-block;
}

/* Responsive adjustments */
@media (max-width: 599px) {
  .error-icon {
    width: 56px;
    height: 56px;
  }

  .error-icon md-icon {
    font-size: 32px;
  }
}
</style>