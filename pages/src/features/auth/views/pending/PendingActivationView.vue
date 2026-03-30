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
          <div class="pending-icon md-flex md-justify-center md-mb-4">
            <md-icon class="pending-icon-large">hourglass_empty</md-icon>
          </div>
          <h2 class="md-typescale-headline-medium md-mb-2">Account Pending Activation</h2>
          <p class="md-typescale-body-large md-mb-6">
            Your account has been created but is not yet activated. Please wait for an administrator
            to activate your account.
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

const router = useRouter();

async function handleLogout() {
  await logout();
  router.push('/login');
}
</script>

<style scoped>
.pending-icon-large {
  font-size: 64px;
  color: var(--md-sys-color-primary);
}
</style>
