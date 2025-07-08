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
    faCreditCard,
    faMoneyBill,
    faIdCard,
    faTriangleExclamation,
    faDumbbell,
    faInfoCircle,
    faSignOutAlt,
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
    console.log('User profile fetched:', data);
    user.value = data.userprofile;
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

    // 进度条动画：10 秒归零
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
            :src="`data:image/png;base64,${user.user_profile_img}`"
            class="profile-picture"
            alt="User profile picture"
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
</style>