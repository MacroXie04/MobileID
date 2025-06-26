<template>
  <div class="main-container">
    <header class="app-header">
      <div class="logo-container">
        <img src="@/assets/images/ucm3.png" alt="UC Merced Logo" class="logo"/>
      </div>
      <div class="logo-container-center">
        <img src="@/assets/images/mobileid_logo.png" alt="MobileID Logo" class="logo"/>
      </div>
      <div class="logo-container"></div>
    </header>
    <div class="header-divider"></div>

    <div v-if="user" class="profile-section">
      <img :src="`data:image/png;base64,${user.user_profile_img}`" class="profile-picture"
           alt="User profile picture">
      <h4 class="white-h4 profile-name">{{ user.name }}</h4>
      <h4 class="white-h4 profile-id">{{ user.student_id }}</h4>

      <button @click="fetchAndShowBarcode" class="btn-trans btn-trans-default"
              :disabled="isLoadingBarcode">
        <b>{{ isLoadingBarcode ? 'Loading...' : 'PAY / Check-in' }}</b>
      </button>
    </div>

    <div v-if="showBarcode" class="barcode-overlay" @click="showBarcode = false">
      <div class="barcode-modal" @click.stop>
        <h3>Your Barcode</h3>
        <canvas ref="barcodeCanvas"></canvas>
        <div class="progress">
          <div class="progress-bar"></div>
        </div>
        <button @click="showBarcode = false" class="btn-trans btn-trans-default"
                style="margin-top: 15px;">Close
        </button>
      </div>
    </div>

    <div class="grid-container">
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="credit-card"/>
        <p>Add Funds</p>
      </a>
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="money-bill"/>
        <p>Balance</p>
      </a>
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="id-card"/>
        <p>Lost My Card</p>
      </a>
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="triangle-exclamation"/>
        <p>Emergency</p>
      </a>
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="dumbbell"/>
        <p>Gym</p>
      </a>
      <a href="#" class="btn-grid">
        <font-awesome-icon icon="info-circle"/>
        <p>Resources</p>
      </a>
      <a @click="logout" href="#" class="btn-grid">
        <font-awesome-icon icon="sign-out-alt"/>
        <p>Log out</p>
      </a>
    </div>

  </div>
</template>

<script setup>
// The <script setup> block remains exactly the same as the previous version.
// No changes to the logic are needed.
import {nextTick, onMounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import apiClient from '@/api';
import bwipjs from 'bwip-js';

import {library} from '@fortawesome/fontawesome-svg-core';
import {
  faCreditCard,
  faDumbbell,
  faIdCard,
  faInfoCircle,
  faMoneyBill,
  faSignOutAlt,
  faTriangleExclamation
} from '@fortawesome/free-solid-svg-icons';
import {FontAwesomeIcon} from '@fortawesome/vue-fontawesome';

library.add(faCreditCard, faMoneyBill, faIdCard, faTriangleExclamation, faDumbbell, faInfoCircle, faSignOutAlt);

const router = useRouter();
const user = ref(null);
const isLoadingBarcode = ref(false);
const showBarcode = ref(false);
const barcodeCanvas = ref(null);

onMounted(async () => {
  try {
    const response = await apiClient.get('/me/');
    user.value = response.data;
  } catch (error) {
    console.error("Failed to fetch user profile:", error);
    if (error.response && error.response.status === 401) {
      logout();
    }
  }
});

const fetchAndShowBarcode = async () => {
  isLoadingBarcode.value = true;
  try {
    const response = await apiClient.get('/generate-barcode/');
    const barcodeData = response.data;
    showBarcode.value = true;
    await nextTick();
    bwipjs.toCanvas(barcodeCanvas.value, {
      bcid: 'pdf417',
      text: barcodeData.barcode,
      scale: 3,
      height: 50,
      includetext: true,
      textxalign: 'center',
    });
  } catch (error) {
    console.error("Failed to generate barcode:", error);
    alert("Could not generate barcode. Please try again.");
  } finally {
    isLoadingBarcode.value = false;
  }
};

const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  router.push('/login');
};
</script>

<style scoped>
/* Most styles are now global in main.css.
   We only keep styles that are TRULY specific to this component's structure. */
.main-container {
  width: 100%;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  width: 100%;
  box-sizing: border-box;
}

.logo-container, .logo-container-center {
  flex: 1;
}

.logo-container-center {
  display: flex;
  justify-content: center;
}

.logo {
  height: 50px;
}

.header-divider {
  border-top: 1px solid rgba(255, 255, 255, 0.5);
  margin: 0 40px;
}

.profile-section {
  text-align: center;
  margin-top: 2em;
  padding: 0 20px;
}

.profile-picture {
  width: 100px;
  height: 100px;
  object-fit: cover;
}

.profile-name {
  margin-top: 0.5em;
}

.profile-id {
  font-weight: 300;
}

.btn-trans-default {
  margin-top: 1.5em;
}

/* Barcode Modal Overlay */
.barcode-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.barcode-modal {
  background-color: #fff;
  padding: 30px;
  border-radius: 10px;
  text-align: center;
  color: #333;
  box-shadow: 0 5px 25px rgba(0, 0, 0, 0.4);
}

.barcode-modal h3 {
  color: #092f44;
}
</style>
