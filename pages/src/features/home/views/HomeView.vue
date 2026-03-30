<template>
  <div
    v-if="pageLoading"
    class="md-loading-container md-flex md-flex-column md-items-center md-justify-center md-theme-dark"
  >
    <md-circular-progress indeterminate></md-circular-progress>
    <p class="md-typescale-body-large md-mt-4">Loading...</p>
  </div>

  <div v-else-if="apiError" class="error-page md-flex md-items-center md-justify-center md-p-6">
    <div class="error-content md-card md-rounded-xl md-p-8 md-text-center md-max-w-lg">
      <div class="error-icon-wrapper md-flex md-justify-center md-mb-6">
        <div class="error-icon md-flex md-items-center md-justify-center">
          <md-icon>error</md-icon>
        </div>
      </div>
      <h2 class="md-typescale-headline-medium md-mb-2">Connection Error</h2>
      <p class="md-typescale-body-large md-mb-6">
        {{ apiError }}
      </p>
      <div class="error-details md-card md-card-filled md-rounded-lg md-p-4 md-mb-6 md-text-left">
        <p class="md-typescale-body-medium md-mb-3">
          Unable to connect to the server. Please check:
        </p>
        <ul class="error-list md-m-0 md-p-0">
          <li class="md-typescale-body-medium">Your internet connection is active</li>
          <li class="md-typescale-body-medium">The server is running and accessible</li>
          <li class="md-typescale-body-medium">Your network allows access to the server</li>
        </ul>
        <p class="error-code md-typescale-label-medium md-mt-4">Error: {{ apiError }}</p>
      </div>
      <md-filled-button class="retry-button" @click="retryConnection">
        <md-icon slot="icon">refresh</md-icon>
        Retry Connection
      </md-filled-button>
    </div>
  </div>

  <div v-else class="home-container">
    <Header />

    <UserProfile
      :avatar-src="avatarSrc"
      :barcode-visible="isBarcodeVisible"
      :is-refreshing-token="isRefreshingToken"
      :loading="homeLoading"
      :profile="profile"
      @generate="handleGenerate"
    />

    <BarcodeDisplay
      ref="barcodeDisplayRef"
      :scanner-detection-enabled="scannerDetectionEnabled"
      :prefer-front-camera="preferFrontCamera"
      @generate="handleGenerate"
    />

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
  useHomeViewSetup,
} from './HomeView.setup.js';

const {
  pageLoading,
  apiError,
  retryConnection,
  profile,
  avatarSrc,
  homeLoading,
  serverStatus,
  barcodeDisplayRef,
  isRefreshingToken,
  scannerDetectionEnabled,
  preferFrontCamera,
  handleGenerate,
  isDetectionActive,
  isBarcodeVisible,
  scannerDetected,
} = useHomeViewSetup();
</script>
