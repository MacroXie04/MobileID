<script setup>
import {computed, nextTick, onMounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import apiClient from '@/api';
import bwipjs from 'bwip-js';
import { getUserStatusSummary, refreshUserStatus } from '../utils/userStatus.js';
import avatarPlaceholder from '@/assets/images/avatar_placeholder.png';

import {library} from '@fortawesome/fontawesome-svg-core';
import {FontAwesomeIcon} from '@fortawesome/vue-fontawesome';
import {
  faCreditCard,
  faDumbbell,
  faIdCard,
  faInfoCircle,
  faMoneyBill,
  faSignOutAlt,
  faTriangleExclamation,
  faCheckCircle,
  faLock,
  faBan,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons';

library.add(
    faCreditCard,
    faMoneyBill,
    faIdCard,
    faTriangleExclamation,
    faDumbbell,
    faInfoCircle,
    faSignOutAlt,
    faCheckCircle,
    faLock,
    faBan,
    faExclamationTriangle,
);

/* ------------------------------ State ------------------------------ */
const router = useRouter();
const user = ref(null);
const serverStatus = ref('Emergency');
const isRequesting = ref(false);
const showBarcode = ref(false);
const barcodeCanvas = ref(null);
const progressBar = ref(null);
const userStatus = ref(null);

const buttonDisabled = computed(() => isRequesting.value);
const buttonLabel = computed(() =>
    isRequesting.value ? 'Processing' : 'PAY / Check-in',
);

// Computed properties for user status display
const statusIcon = computed(() => {
  if (!userStatus.value) return 'exclamation-triangle';
  
  switch (userStatus.value.status.status) {
    case 'active':
      return 'check-circle';
    case 'locked':
      return 'lock';
    case 'disabled':
      return 'ban';
    default:
      return 'exclamation-triangle';
  }
});

const statusClass = computed(() => {
  if (!userStatus.value) return 'text-warning';
  
  switch (userStatus.value.status.status) {
    case 'active':
      return 'text-success';
    case 'locked':
      return 'text-warning';
    case 'disabled':
      return 'text-danger';
    default:
      return 'text-warning';
  }
});

const statusMessage = computed(() => {
  if (!userStatus.value) return 'Status Unknown';
  
  return userStatus.value.status.message || 'No status message';
});

/* ------------------------------ Fetch profile ---------------------- */
onMounted(async () => {
  try {
    // Get user status information first from localStorage if available
    userStatus.value = getUserStatusSummary();
    
    // Refresh status from API to ensure it's current and get updated user data
    await refreshUserStatus();
    
    // Get updated status and user profile from localStorage after refresh
    userStatus.value = getUserStatusSummary();
    const currentUserProfile = userStatus.value.profile;
    
    // Set user data with default values if userprofile is not found
    user.value = currentUserProfile && Object.keys(currentUserProfile).length > 0 ? currentUserProfile : {
      name: 'Unknown User',
      information_id: 'N/A',
      user_profile_img: ''
    };
    
    console.log('User profile loaded:', user.value);
    
  } catch (err) {
    console.error('Fetch profile failed:', err);
    if (err.response?.status === 401) logout();
  }
});

/* ------------------------------ Generate barcode ------------------- */
async function fetchAndShowBarcode() {
  if (isRequesting.value) return;
  isRequesting.value = true;
  serverStatus.value = 'Processing';

  try {
    const {data} = await apiClient.post('/generate_barcode/');
    if (data.status !== 'success') throw new Error(data.message);

    showBarcode.value = true;
    await nextTick();

    bwipjs.toCanvas(barcodeCanvas.value, {
      bcid: 'pdf417',
      text: data.barcode,
      scaleX: 2,
      scaleY: 2,
      includetext: false,
      padding: 0,
      backgroundcolor: 'FFFFFF',
    });

    // progress bar animation: 10 seconds to 0%
    progressBar.value.style.transition = 'none';
    progressBar.value.style.width = '100%';
    requestAnimationFrame(() => {
      progressBar.value.style.transition = 'width 10s linear';
      progressBar.value.style.width = '0%';
    });
    setTimeout(resetDisplay, 10_400);

    serverStatus.value = data.content || 'OK';
  } catch (err) {
    console.error('Generate barcode error:', err);
    serverStatus.value = 'Error';
    alert('Could not generate barcode. Please try again.');
  } finally {
    isRequesting.value = false;
  }
}

/* ------------------------------ Helpers ---------------------------- */
function handleImageError(event) {
  // Set a fallback image if the profile image fails to load
  event.target.src = avatarPlaceholder;
}

function resetDisplay() {
  showBarcode.value = false;
  serverStatus.value = 'Emergency';
  progressBar.value.style.transition = 'none';
  progressBar.value.style.width = '100%';
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_profile');
  localStorage.removeItem('user_status');
  router.push('/login');
}
</script>

<template>
  <div class="main-container">
    <!-- Header -->
    <header class="app-header">
      <div class="logo-container">
        <img alt="UC Merced Logo" class="logo" src="@/assets/images/ucm3.png"/>
      </div>
      <div class="logo-container-center">
        <img alt="MobileID Logo" class="logo" src="@/assets/images/mobileid_logo.png"/>
      </div>
      <div class="logo-container"/>
    </header>
    <div class="header-divider"/>

    <!-- Profile information -->
    <div v-if="user" class="profile-section">
      <a href="/profile_edit">
        <img
            :src="user.user_profile_img ? `data:image/png;base64,${user.user_profile_img}` : avatarPlaceholder"
            class="profile-picture"
            alt="User profile picture"
            @error="handleImageError"
        />
      </a>

      <h4 class="white-h4" style="padding-top: 10px">{{ user.name }}</h4>
      <h4 id="student-id" class="white-h4">{{ user.information_id }}</h4>

      <transition name="fade">
        <div v-if="showBarcode" class="barcode-wrapper">
          <canvas ref="barcodeCanvas"></canvas>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="showBarcode" class="progress">
          <div ref="progressBar" class="progress-bar"></div>
        </div>
      </transition>

      <transition name="fade">
        <button
            v-if="!showBarcode"
            :disabled="buttonDisabled"
            class="btn-trans btn-trans-default"
            style="margin-top: 10px"
            @click="fetchAndShowBarcode"
        >
          <b>{{ buttonLabel }}</b>
        </button>
      </transition>
    </div>

    <!-- Grid -->
    <div class="grid-container">
      <a class="btn-grid" href="/profile_edit">
        <FontAwesomeIcon icon="credit-card"/>
        <p>Add Funds</p>
      </a>
      <a class="btn-grid" href="/manage_barcode">
        <FontAwesomeIcon icon="money-bill"/>
        <p>Balance</p>
      </a>
      <a class="btn-grid" href="/barcode_settings">
        <FontAwesomeIcon icon="id-card"/>
        <p>Lost My Card</p>
      </a>
      <a class="btn-grid" href="#">
        <FontAwesomeIcon icon="triangle-exclamation"/>
        <p>{{ serverStatus }}</p>
      </a>
      <a class="btn-grid" href="#">
        <FontAwesomeIcon icon="dumbbell"/>
        <p>Gym</p>
      </a>
      <a class="btn-grid" href="#">
        <FontAwesomeIcon icon="info-circle"/>
        <p>Resources</p>
      </a>
      <a class="btn-grid" href="#" @click="logout">
        <FontAwesomeIcon icon="sign-out-alt"/>
        <p>Log out</p>
      </a>
    </div>
  </div>
</template>

<style scoped>
@import '@/assets/css/HomeView.css';

/* Add styles for status indicator */
.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 10px 0;
  padding: 8px 16px;
  border-radius: 20px;
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  font-size: 0.9rem;
  font-weight: 500;
}

.status-icon {
  font-size: 1rem;
}

.status-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* Responsive adjustments for status indicator */
@media (max-width: 768px) {
  .status-indicator {
    font-size: 0.8rem;
    padding: 6px 12px;
  }
  
  .status-text {
    max-width: 150px;
  }
}
</style>