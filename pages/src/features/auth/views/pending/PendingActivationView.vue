<template>
  <div class="auth-container">
    <div class="auth-background">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <main class="auth-main">
      <div class="auth-card md-card md-rounded-xl">
        <div class="pending-content md-text-center">
          <h2 class="md-typescale-headline-medium md-mb-2">Access Denied</h2>
          <p class="md-typescale-body-large md-mb-6">
            You do not have permission to access this page.
          </p>
          <md-filled-button class="submit-button" @click="handleLogout">
            <md-icon slot="icon">logout</md-icon>
            Sign Out
          </md-filled-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { logout } from '@shared/api/auth';
import '@/assets/styles/auth/auth-merged.css';

const router = useRouter();

async function handleLogout() {
  await logout();
  router.push('/login');
}
</script>
