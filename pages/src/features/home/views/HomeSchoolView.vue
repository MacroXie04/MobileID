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
    <BarcodeDisplay
      ref="barcodeDisplayRef"
      :scanner-detection-enabled="scannerDetectionEnabled"
      :prefer-front-camera="preferFrontCamera"
      @generate="handleGenerate"
    />

    <!-- Grid Menu Component -->
    <GridMenu
      :server-status="serverStatus"
      :scanner-detection-enabled="scannerDetectionEnabled"
      :is-detection-active="isDetectionActive"
      :scanner-detected="scannerDetected"
    />
  </div>
</template>

<script setup>
import {
  Header,
  UserProfile,
  BarcodeDisplay,
  GridMenu,
  useHomeSchoolViewSetup,
} from './HomeSchoolView.setup.js';

const {
  profile,
  avatarSrc,
  loading,
  serverStatus,
  barcodeDisplayRef,
  isRefreshingToken,
  scannerDetectionEnabled,
  preferFrontCamera,
  handleGenerate,
  isDetectionActive,
  scannerDetected,
} = useHomeSchoolViewSetup();
</script>
