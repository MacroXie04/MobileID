<template>
  <section class="dashboard-card camera-settings-card md-mb-6">
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>sensors</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small">Scanner Detection</h2>
      </div>
    </div>

    <div class="settings-content">
      <!-- Camera Permission Required Banner -->
      <div v-if="!hasCameraPermission" class="permission-banner">
        <div class="permission-banner-icon">
          <md-icon>videocam_off</md-icon>
        </div>
        <div class="permission-banner-content">
          <span class="permission-banner-title">Camera Permission Required</span>
          <span class="permission-banner-desc"
            >Grant camera access to enable scanner detection</span
          >
        </div>
        <md-filled-tonal-button :disabled="isRequestingPermission" @click="requestCameraPermission">
          <md-icon slot="icon">{{
            isRequestingPermission ? 'hourglass_empty' : 'videocam'
          }}</md-icon>
          {{ isRequestingPermission ? 'Requesting...' : 'Allow' }}
        </md-filled-tonal-button>
      </div>

      <!-- Camera Preview Section (moved above settings) -->
      <div v-if="scannerDetectionEnabled && hasCameraPermission" class="camera-preview-section">
        <div class="section-header">
          <md-icon>preview</md-icon>
          <span>Detection</span>
        </div>

        <!-- Camera Preview -->
        <div class="camera-wrapper" :class="{ active: isDetectionActive }">
          <video ref="videoElement" class="camera-video" autoplay playsinline muted></video>
          <canvas ref="detectionCanvas" class="detection-canvas"></canvas>

          <!-- Status Badge -->
          <div class="status-overlay">
            <div class="status-badge" :class="statusClass">
              <md-icon>{{ statusIcon }}</md-icon>
              <span>{{ detectionStatus }}</span>
            </div>
          </div>

          <!-- Detected Objects -->
          <div v-if="detectedObjects.length > 0" class="detected-list">
            <div v-for="obj in detectedObjects" :key="obj.class" class="detected-tag">
              <md-icon>sensors</md-icon>
              <span>{{ obj.class }} {{ Math.round(obj.score * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- Controls -->
        <div class="camera-controls">
          <md-filled-tonal-button :disabled="isModelLoading" @click="toggleDetection">
            <md-icon slot="icon">{{ isDetectionActive ? 'stop' : 'play_arrow' }}</md-icon>
            {{ isDetectionActive ? 'Stop' : 'Start Test' }}
          </md-filled-tonal-button>
        </div>

        <!-- Loading -->
        <div v-if="isModelLoading" class="model-loading">
          <md-circular-progress indeterminate></md-circular-progress>
          <span>Loading AI model...</span>
        </div>

        <!-- Info Hint -->
        <div class="info-hint">
          <md-icon>info</md-icon>
          <span>Detection runs automatically at barcode display page</span>
        </div>
      </div>

      <!-- Scanner Detection Toggle -->
      <md-list>
        <md-list-item :class="{ 'disabled-item': !hasCameraPermission }">
          <md-icon slot="start">sensors</md-icon>
          <div slot="headline">Enable Scanner Detection</div>
          <div slot="supporting-text">
            {{
              hasCameraPermission
                ? 'Auto-display barcode when scanner is detected'
                : 'Camera permission required to enable this feature'
            }}
          </div>
          <div slot="end">
            <md-switch
              :disabled="!hasCameraPermission"
              :selected="scannerDetectionEnabled"
              @change="(e) => $emit('update-scanner-detection', e.target.selected)"
            ></md-switch>
          </div>
        </md-list-item>

        <md-divider inset></md-divider>

        <md-list-item
          :class="{ 'disabled-item': !scannerDetectionEnabled || !hasCameraPermission }"
        >
          <md-icon slot="start">videocam</md-icon>
          <div slot="headline">Default Camera</div>
          <div slot="supporting-text">
            {{
              cameras.length > 0
                ? 'Select which camera to use for detection'
                : 'No cameras available'
            }}
          </div>
          <div slot="end">
            <md-outlined-select
              v-if="cameras.length > 0"
              :disabled="!scannerDetectionEnabled || !hasCameraPermission"
              :value="selectedCameraId"
              class="camera-select-inline"
              @change="handleCameraChange"
            >
              <md-select-option
                v-for="camera in cameras"
                :key="camera.deviceId"
                :value="camera.deviceId"
              >
                <div slot="headline">{{ formatCameraLabel(camera) }}</div>
              </md-select-option>
            </md-outlined-select>
            <span v-else class="no-camera-text">No cameras</span>
          </div>
        </md-list-item>
      </md-list>
    </div>
  </section>
</template>

<script setup>
import {
  propsDefinition,
  emitsDefinition,
  useCameraSettingsCardSetup,
} from './CameraSettingsCard.setup.js';

const props = defineProps(propsDefinition);
defineEmits(emitsDefinition);

const {
  videoElement,
  detectionCanvas,
  isRequestingPermission,
  isDetectionActive,
  isModelLoading,
  detectionStatus,
  cameras,
  selectedCameraId,
  detectedObjects,
  hasCameraPermission,
  requestCameraPermission,
  toggleDetection,
  handleCameraChange,
  formatCameraLabel,
  statusClass,
  statusIcon,
} = useCameraSettingsCardSetup({ props });
</script>
