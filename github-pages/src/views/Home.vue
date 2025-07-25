<!-- src/views/Home.vue -->
<template>
  <div v-if="loading" class="loading-container">
    <div class="loading-spinner">
      <svg class="circular-progress" viewBox="0 0 50 50">
        <circle class="progress-circle" cx="25" cy="25" r="20" fill="none" stroke-width="4"/>
      </svg>
    </div>
    <p class="loading-text">Loading...</p>
  </div>

  <!-- Based on user groups -->
  <HomeSchool v-else-if="groups.includes('School')" />
  <HomeUser   v-else-if="groups.includes('User')"   />
  <div v-else class="error-page">
    <div class="error-content">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
      </div>
      <h2 class="error-title">连接错误</h2>
      <p class="error-message">{{ window.apiError || '未知用户组，请联系管理员' }}</p>
      <div class="error-details" v-if="window.apiError">
        <p>无法连接到服务器，请检查：</p>
        <ul>
          <li>服务器是否正在运行</li>
          <li>网络连接是否正常</li>
          <li>防火墙设置是否正确</li>
        </ul>
      </div>
      <button class="retry-button" @click="retryConnection">
        <svg class="retry-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
        </svg>
        重试连接
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import HomeSchool from "./HomeSchool.vue";
import HomeUser from "./HomeUser.vue";

const loading = ref(true);
const groups  = ref([]);

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
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1.5rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
}

.circular-progress {
  animation: rotate 2s linear infinite;
}

.progress-circle {
  stroke: var(--md-sys-color-primary);
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.loading-text {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 1rem;
  font-weight: 400;
  margin: 0;
}

.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--md-sys-color-background);
}

.error-content {
  background: var(--md-sys-color-surface-container-lowest);
  border-radius: var(--md-sys-shape-corner-extra-large);
  padding: 3rem 2rem;
  max-width: 480px;
  width: 100%;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: var(--md-sys-color-error-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon svg {
  width: 48px;
  height: 48px;
  fill: var(--md-sys-color-on-error-container);
}

.error-title {
  color: var(--md-sys-color-on-surface);
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.error-message {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 1.125rem;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.error-details {
  background: var(--md-sys-color-surface-container);
  border-radius: var(--md-sys-shape-corner-medium);
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
}

.error-details p {
  color: var(--md-sys-color-on-surface-variant);
  margin: 0 0 0.75rem;
  font-weight: 500;
}

.error-details ul {
  margin: 0;
  padding-left: 1.5rem;
  color: var(--md-sys-color-on-surface-variant);
}

.error-details li {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.retry-button {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border: none;
  border-radius: var(--md-sys-shape-corner-full);
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.retry-button:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.retry-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.retry-icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .error-content {
    padding: 2rem 1.5rem;
  }
  
  .error-icon {
    width: 64px;
    height: 64px;
  }
  
  .error-icon svg {
    width: 36px;
    height: 36px;
  }
  
  .error-title {
    font-size: 1.5rem;
  }
  
  .error-message {
    font-size: 1rem;
  }
}
</style>