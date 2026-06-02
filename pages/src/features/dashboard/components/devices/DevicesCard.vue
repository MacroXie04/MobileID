<template>
  <section class="dashboard-card md-mb-6">
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>devices</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small">Logged-in Devices</h2>
      </div>
      <md-icon-button v-if="!loading" class="refresh-button" @click="fetchDevices">
        <md-icon>refresh</md-icon>
      </md-icon-button>
    </div>

    <div class="devices-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container md-flex md-flex-column md-items-center md-py-8">
        <md-circular-progress indeterminate></md-circular-progress>
        <span class="md-typescale-body-medium md-mt-4">Loading devices...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container md-flex md-flex-column md-items-center md-py-8">
        <md-icon class="error-icon">error</md-icon>
        <span class="md-typescale-body-medium md-mt-2">{{ error }}</span>
        <md-filled-tonal-button class="md-mt-4" @click="fetchDevices">
          <md-icon slot="icon">refresh</md-icon>
          Try Again
        </md-filled-tonal-button>
      </div>

      <!-- Devices List -->
      <template v-else>
        <!-- Current Device Section -->
        <div v-if="currentDevice" class="devices-section md-mb-6">
          <div class="section-header">
            <md-icon>smartphone</md-icon>
            <span>Current Device</span>
          </div>
          <DeviceCard
            :device="currentDevice"
            :is-current="true"
            :revoking="revoking"
            :get-device-icon="getDeviceIcon"
            :format-relative-time="formatRelativeTime"
            :format-expiration-time="formatExpirationTime"
          />
        </div>

        <!-- Other Devices Section -->
        <div v-if="hasOtherDevices" class="devices-section">
          <div class="section-header">
            <md-icon>devices_other</md-icon>
            <span>Other Devices ({{ otherDevices.length }})</span>
            <md-filled-tonal-button
              class="revoke-all-button"
              :disabled="revoking !== null"
              @click="revokeAllOtherDevices"
            >
              <md-icon slot="icon">logout</md-icon>
              {{ revoking === 'all' ? 'Logging out...' : 'Log out all' }}
            </md-filled-tonal-button>
          </div>

          <div class="devices-list">
            <DeviceCard
              v-for="device in otherDevices"
              :key="device.id"
              :device="device"
              :revoking="revoking"
              :get-device-icon="getDeviceIcon"
              :format-relative-time="formatRelativeTime"
              :format-expiration-time="formatExpirationTime"
              @revoke="revokeDevice"
            />
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="!currentDevice && !hasOtherDevices"
          class="empty-state md-flex md-flex-column md-items-center md-py-8"
        >
          <md-icon class="empty-icon">devices_off</md-icon>
          <span class="md-typescale-body-medium md-mt-2">No devices found</span>
        </div>

        <!-- Single Device Info -->
        <div
          v-else-if="!hasOtherDevices"
          class="info-banner md-flex md-items-center md-gap-3 md-mt-4"
        >
          <md-icon>info</md-icon>
          <span class="md-typescale-body-small"
            >You are only logged in on this device. Your session will expire
            {{ formatExpirationTime(currentDevice?.expires_at) }}.</span
          >
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import DeviceCard from './DeviceCard.vue';
import { useDevicesCardSetup } from './DevicesCard.setup';

const {
  loading,
  error,
  revoking,
  currentDevice,
  otherDevices,
  hasOtherDevices,
  fetchDevices,
  revokeDevice,
  revokeAllOtherDevices,
  getDeviceIcon,
  formatRelativeTime,
  formatExpirationTime,
} = useDevicesCardSetup();
</script>
