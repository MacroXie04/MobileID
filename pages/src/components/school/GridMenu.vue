<template>
  <!-- 3 × 3 Grid -->
  <div class="grid-wrapper">
    <div class="grid-container">
      <!-- Row 1 -->
      <a class="btn-grid" href="/profile/edit" @click.prevent="handleEditProfile">
        <i class="fa fa-credit-card fa-2x"></i>
        <p>Add Funds</p>
      </a>
      <a class="btn-grid" href="/dashboard" @click.prevent="handleBarcodeDashboard">
        <i class="fa fa-money-bill fa-2x"></i>
        <p>Balance</p>
      </a>
      <a id="lost-my-card" class="btn-grid" href="#">
        <i class="fa fa-id-card fa-2x"></i>
        <p>Lost My Card</p>
      </a>

      <!-- Row 2 -->
      <a id="emergency" class="btn-grid" href="#">
        <i class="fa fa-exclamation-triangle fa-2x"></i>
        <p>{{ serverStatus }}</p>
      </a>
      <a id="gym" class="btn-grid" href="#">
        <i class="fa fa-dumbbell fa-2x"></i>
        <p>Gym</p>
      </a>
      <a id="resource" class="btn-grid" href="#">
        <i class="fa fa-info fa-2x"></i>
        <p>Resources</p>
      </a>

      <!-- Row 3 -->
      <a class="btn-grid" href="https://alynx.ucmerced.edu/" rel="noopener noreferrer" target="_blank">
        <i class="fa fa-link fa-2x"></i>
        <p>Alynx</p>
      </a>
      <a class="btn-grid" href="#" @click.prevent="handleLogout">
        <i class="fa fa-sign-out-alt fa-2x"></i>
        <p>Log out</p>
      </a>
    </div>
  </div>
</template>

<script setup>
import {toRefs} from 'vue';
import {useRouter} from 'vue-router';
import {logout} from '@/api/auth';
import {clearAuthCookies, clearAuthStorage} from '@/utils/cookie';

// CSS
import '@/assets/css/school-merged.css';

const router = useRouter();

// Props
const props = defineProps({
  serverStatus: {
    type: String,
    default: "Emergency"
  }
});

// Destructure props for reactivity
const {serverStatus} = toRefs(props);

// Functions
function handleEditProfile() {
  router.push('/profile/edit');
}

function handleBarcodeDashboard() {
  router.push('/dashboard');
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
      const {clearUserProfile} = await import('@/composables/useUserInfo');
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

