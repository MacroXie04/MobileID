<script setup>
import {computed, nextTick, onMounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import apiClient from '@/api';
import bwipjs from 'bwip-js';

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
} from '@fortawesome/free-solid-svg-icons';

library.add(
  faCreditCard, faMoneyBill, faIdCard, faTriangleExclamation,
  faDumbbell, faInfoCircle, faSignOutAlt,
);

/* ------------------------------ State ------------------------------ */
const router = useRouter();
const user = ref(null);
const serverStatus = ref('Emergency');
const isRequesting = ref(false);
const showBarcode = ref(false);
const barcodeCanvas = ref(null);
const progressBar = ref(null);

const buttonDisabled = computed(() => isRequesting.value);
const buttonLabel = computed(() =>
  isRequesting.value ? 'Processing' : 'PAY / Check-in',
);

/* ------------------------------ Fetch profile ---------------------- */
onMounted(async () => {
  try {
    const {data} = await apiClient.get('/me/');
    user.value = data;
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

    progressBar.value.style.transition = 'none';
    progressBar.value.style.width = '100%';
    requestAnimationFrame(() => {
      progressBar.value.style.transition = 'width 10s linear';
      progressBar.value.style.width = '0%';
    });
    setTimeout(resetDisplay, 10400);

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
function resetDisplay() {
  showBarcode.value = false;
  serverStatus.value = 'Emergency';
  progressBar.value.style.transition = 'none';
  progressBar.value.style.width = '100%';
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  router.push('/login');
}
</script>

<template>
  <div class="main-container">
    <!-- Header -->
    <header class="app-header">
      <div class="logo-container">
        <img src="@/assets/images/ucm3.png" class="logo" alt="UC Merced Logo"/>
      </div>
      <div class="logo-container-center">
        <img src="@/assets/images/mobileid_logo.png" class="logo" alt="MobileID Logo"/>
      </div>
      <div class="logo-container"></div>
    </header>
    <div class="header-divider"></div>

    <!-- Profile -->
    <div v-if="user" class="profile-section">
      <img
        :src="`data:image/png;base64,${user.user_profile_img}`"
        class="profile-picture"
        alt="User profile picture"
      />
      <h4 class="white-h4 profile-info">{{ user.name }}</h4>
      <h4 class="white-h4 profile-info" style="margin-top: 0 !important;">{{ user.student_id }}</h4>

      <transition name="fade">
        <div v-if="showBarcode" class="barcode-wrapper">
          <canvas ref="barcodeCanvas"></canvas>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="showBarcode" class="progress">
          <div class="progress-bar" ref="progressBar"></div>
        </div>
      </transition>

      <transition name="fade">
        <button
          v-if="!showBarcode"
          @click="fetchAndShowBarcode"
          class="btn-trans btn-trans-default"
          :disabled="buttonDisabled"
          style="margin-top: 20px"
        >
          <b>{{ buttonLabel }}</b>
        </button>
      </transition>
    </div>

    <!-- Grid -->
    <div class="grid-container">
      <a href="/profile_edit" class="btn-grid">
        <FontAwesomeIcon icon="credit-card"/>
        <p>Add Funds</p></a>
      <a href="#" class="btn-grid">
        <FontAwesomeIcon icon="money-bill"/>
        <p>Balance</p></a>
      <a href="#" class="btn-grid">
        <FontAwesomeIcon icon="id-card"/>
        <p>Lost My Card</p></a>
      <a href="#" class="btn-grid">
        <FontAwesomeIcon icon="triangle-exclamation"/>
        <p>{{ serverStatus }}</p></a>
      <a href="#" class="btn-grid">
        <FontAwesomeIcon icon="dumbbell"/>
        <p>Gym</p></a>
      <a href="#" class="btn-grid">
        <FontAwesomeIcon icon="info-circle"/>
        <p>Resources</p></a>
      <a @click="logout" href="#" class="btn-grid">
        <FontAwesomeIcon icon="sign-out-alt"/>
        <p>Log out</p></a>
    </div>
  </div>
</template>

<style scoped>
@import '@/assets/css/HomeView.css';
</style>
