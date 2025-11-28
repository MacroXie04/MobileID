<template>
  <section class="dashboard-card md-mb-6">
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>devices</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small">Logged-in Devices</h2>
        <p class="md-typescale-body-small header-subtitle">
          Manage your active sessions across devices
        </p>
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
          <div class="device-card current-device">
            <div class="device-icon-wrapper">
              <md-icon>{{ getDeviceIcon(currentDevice.device_type) }}</md-icon>
            </div>
            <div class="device-info">
              <div class="device-name md-typescale-title-medium">
                {{ currentDevice.device_name }}
                <md-assist-chip class="current-badge" has-icon>
                  <md-icon slot="icon">check_circle</md-icon>
                  Current
                </md-assist-chip>
              </div>
              <div class="device-details md-typescale-body-small">
                <span v-if="currentDevice.ip_address" class="detail-item">
                  <md-icon>location_on</md-icon>
                  {{ currentDevice.ip_address }}
                </span>
                <span class="detail-item">
                  <md-icon>login</md-icon>
                  Logged in {{ formatRelativeTime(currentDevice.created_at) }}
                </span>
                <span class="detail-item expiration">
                  <md-icon>schedule</md-icon>
                  {{ formatExpirationTime(currentDevice.expires_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Other Devices Section -->
        <div v-if="hasOtherDevices" class="devices-section">
          <div class="section-header">
            <md-icon>devices_other</md-icon>
            <span>Other Devices ({{ otherDevices.length }})</span>
            <md-filled-tonal-button class="revoke-all-button md-ml-auto" @click="handleRevokeAll">
              <md-icon slot="icon">logout</md-icon>
              Log Out All
            </md-filled-tonal-button>
          </div>

          <div class="devices-list">
            <div v-for="device in otherDevices" :key="device.id" class="device-card">
              <div class="device-icon-wrapper">
                <md-icon>{{ getDeviceIcon(device.device_type) }}</md-icon>
              </div>
              <div class="device-info">
                <div class="device-name md-typescale-title-medium">
                  {{ device.device_name }}
                </div>
                <div class="device-details md-typescale-body-small">
                  <span v-if="device.ip_address" class="detail-item">
                    <md-icon>location_on</md-icon>
                    {{ device.ip_address }}
                  </span>
                  <span class="detail-item">
                    <md-icon>login</md-icon>
                    {{ formatRelativeTime(device.created_at) }}
                  </span>
                  <span class="detail-item expiration">
                    <md-icon>schedule</md-icon>
                    {{ formatExpirationTime(device.expires_at) }}
                  </span>
                </div>
              </div>
              <div class="device-actions">
                <md-filled-tonal-button
                  :disabled="revoking[device.id]"
                  class="revoke-button"
                  @click="handleRevoke(device.id)"
                >
                  <md-icon v-if="revoking[device.id]" slot="icon">hourglass_empty</md-icon>
                  <md-icon v-else slot="icon">logout</md-icon>
                  {{ revoking[device.id] ? 'Logging out...' : 'Log Out' }}
                </md-filled-tonal-button>
              </div>
            </div>
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

<script setup>
import { useDevicesCardSetup } from './DevicesCard.setup.js';

const {
  loading,
  error,
  revoking,
  currentDevice,
  otherDevices,
  hasOtherDevices,
  fetchDevices,
  getDeviceIcon,
  formatRelativeTime,
  formatExpirationTime,
  handleRevoke,
  handleRevokeAll,
} = useDevicesCardSetup();
</script>
