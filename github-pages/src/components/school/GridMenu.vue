<template>
  <!-- 3 × 3 Grid -->
  <div class="grid-wrapper">
    <div class="grid-container">
      <!-- Row 1 -->
      <a href="/profile/edit" class="btn-grid" @click.prevent="handleEditProfile">
        <i class="fa fa-credit-card fa-2x"></i>
        <p>Add Funds</p>
      </a>
      <a href="/barcode/dashboard" class="btn-grid" @click.prevent="handleBarcodeDashboard">
        <i class="fa fa-money-bill fa-2x"></i>
        <p>Balance</p>
      </a>
      <a id="lost-my-card" href="#" class="btn-grid">
        <i class="fa fa-id-card fa-2x"></i>
        <p>Lost My Card</p>
      </a>

      <!-- Row 2 -->
      <a id="emergency" href="#" class="btn-grid">
        <i class="fa fa-exclamation-triangle fa-2x"></i>
        <p>{{ serverStatus }}</p>
      </a>
      <a id="gym" href="#" class="btn-grid">
        <i class="fa fa-dumbbell fa-2x"></i>
        <p>Gym</p>
      </a>
      <a id="resource" href="#" class="btn-grid">
        <i class="fa fa-info fa-2x"></i>
        <p>Resources</p>
      </a>

      <!-- Row 3 -->
      <a href="https://alynx.ucmerced.edu/" target="_blank" class="btn-grid">
        <i class="fa fa-link fa-2x"></i>
        <p>Alynx</p>
      </a>
      <a href="#" class="btn-grid" @click.prevent="handleLogout">
        <i class="fa fa-sign-out-alt fa-2x"></i>
        <p>Log out</p>
      </a>
    </div>
  </div>
</template>

<script setup>
import { toRefs } from 'vue';
import { useRouter } from 'vue-router';
import { logout } from '@/api/auth';
import { clearAuthCookies, clearAuthStorage } from '@/utils/cookie';

const router = useRouter();

// Props
const props = defineProps({
  serverStatus: {
    type: String,
    default: "Emergency"
  }
});

// Destructure props for reactivity
const { serverStatus } = toRefs(props);

// Functions
function handleEditProfile() {
  router.push('/profile/edit');
}

function handleBarcodeDashboard() {
  router.push('/barcode/dashboard');
}

async function handleLogout() {
  try {
    // Call logout API
    await logout();
    
    // Clear authentication data
    clearAuthCookies();
    clearAuthStorage();
    
    // Clear user profile cache
    try {
      const { clearUserProfile } = await import('@/composables/useUserInfo');
      clearUserProfile();
    } catch (error) {
      console.warn("Could not clear user profile cache:", error);
    }
    
    // Redirect to login page
    router.push('/login');
  } catch (error) {
    console.error('Logout failed:', error);
    // Even if API call fails, still clear local data and redirect
    clearAuthCookies();
    clearAuthStorage();
    router.push('/login');
  }
}
</script>

<style scoped>
/* Container that centers the whole grid */
.grid-wrapper {
  margin: auto;
  max-width: 320px;
}

/* 3 × 3 grid */
.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 16px;

  /* keep borders/padding inside the 320 px box */
  box-sizing: border-box;
  overflow: hidden;
}

/* Grid buttons */
.btn-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  width: 100%;
  height: 100%;
  padding: 20px 10px;
  min-height: 80px;

  text-decoration: none;
  color: inherit;

  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;

  /* keep borders/padding inside their grid cell */
  box-sizing: border-box;
}

/* Icon colour */
.btn-grid i {
  margin-bottom: 8px;
  color: #bf9c44;
}

/* Label text */
.btn-grid p {
  margin: 0;
  font-size: 12px;
  text-align: center;
  color: #bf9c44;
}
</style>
