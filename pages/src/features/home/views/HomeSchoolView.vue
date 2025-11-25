<template>
  <div class="home-school-container">
    <!-- Header Component -->
    <Header />

    <!-- User Profile Component -->
    <UserProfile
      :avatar-src="avatarSrc"
      :is-refreshing-token="isRefreshingToken"
      :loading="loading"
      :profile="profile"
      @generate="handleGenerate"
    />

    <!-- Barcode Display Component -->
    <BarcodeDisplay ref="barcodeDisplayRef" />

    <!-- Grid Menu Component -->
    <GridMenu :server-status="serverStatus" />
  </div>
</template>

<script setup>
import { useHomeSchoolLogic } from '@home/composables/useHomeSchoolLogic.js';

// CSS Imports
import '@/assets/styles/home/HomeSchool.css';
// Import Font Awesome for this page (needed for GridMenu component)
import '@fortawesome/fontawesome-free/css/all.min.css';

// Components
import Header from '@school/components/Header.vue';
import UserProfile from '@school/components/UserProfile.vue';
import BarcodeDisplay from '@school/components/BarcodeDisplay.vue';
import GridMenu from '@school/components/GridMenu.vue';

const {
  profile,
  avatarSrc,
  loading,
  serverStatus,
  barcodeDisplayRef,
  isRefreshingToken,
  handleGenerate,
} = useHomeSchoolLogic();
</script>
