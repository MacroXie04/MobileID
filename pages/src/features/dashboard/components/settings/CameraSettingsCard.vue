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
      <CameraPermissionBanner
        v-if="!hasCameraPermission"
        title="Camera Permission Required"
        description="Grant camera access to enable scanner detection"
        :is-requesting="isRequestingPermission"
        @request="requestCameraPermission"
      />

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

      <!-- Scanner Detection Settings -->
      <ScannerDetectionSettingsList
        :scanner-detection-enabled="scannerDetectionEnabled"
        :has-camera-permission="hasCameraPermission"
        :cameras="cameras"
        :selected-camera-id="selectedCameraId"
        @update-scanner-detection="(val) => $emit('update-scanner-detection', val)"
        @camera-change="handleCameraChangeId"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import CameraPermissionBanner from '@dashboard/components/shared/CameraPermissionBanner.vue';
import ScannerDetectionSettingsList from './camera/ScannerDetectionSettingsList.vue';
import {
  propsDefinition,
  emitsDefinition,
  useCameraSettingsCardSetup,
} from './CameraSettingsCard.setup';

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
  handleCameraChangeId,
  statusClass,
  statusIcon,
} = useCameraSettingsCardSetup({ props });
</script>

<style scoped>
/* Camera Preview Section — the video/canvas detection stream lives in this
   parent (its template refs bind to composable-owned refs), so these rules
   are co-located here rather than in a child component. */
.camera-preview-section {
  margin-bottom: var(--md-sys-spacing-4);
  padding: var(--md-sys-spacing-4);
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
}

/* Camera Preview Wrapper */
.camera-wrapper {
  position: relative;
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
  background: #000;
  border: 2px solid var(--md-sys-color-outline-variant);
  transition: all 0.3s ease;
}

.camera-wrapper.active {
  border-color: var(--md-sys-color-primary);
  box-shadow: var(--md-elevation-2);
}

.camera-video {
  width: 100%;
  height: auto;
  display: block;
  transform: scaleX(-1);
  max-height: 220px;
  object-fit: cover;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  transform: scaleX(-1);
}

.status-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--md-sys-shape-corner-small);
  font-size: 11px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}

.status-badge.loading {
  background: rgba(255, 152, 0, 0.85);
}

.status-badge.active {
  background: rgba(76, 175, 80, 0.85);
}

.status-badge md-icon {
  font-size: 12px;
  --md-icon-size: 12px;
}

.detected-list {
  position: absolute;
  bottom: 8px;
  left: 8px;
  right: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detected-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  border-radius: var(--md-sys-shape-corner-extra-small);
  font-size: 10px;
  font-weight: 600;
  background: rgba(76, 175, 80, 0.9);
  color: white;
}

.detected-tag md-icon {
  font-size: 10px;
  --md-icon-size: 10px;
}

/* Camera Controls */
.camera-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-sys-spacing-2);
  margin-top: var(--md-sys-spacing-3);
  flex-wrap: wrap;
}

.model-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-sys-spacing-2);
  padding: var(--md-sys-spacing-3);
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-body-small-size);
}

/* Info Hint */
.info-hint {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  margin-top: var(--md-sys-spacing-3);
  padding: var(--md-sys-spacing-2) var(--md-sys-spacing-3);
  background: var(--md-sys-color-surface-container);
  border-radius: var(--md-sys-shape-corner-small);
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}

.info-hint md-icon {
  font-size: 14px;
  --md-icon-size: 14px;
  color: var(--md-sys-color-outline);
}
</style>
