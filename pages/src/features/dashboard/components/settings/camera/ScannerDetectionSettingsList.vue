<template>
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

    <md-list-item :class="{ 'disabled-item': !scannerDetectionEnabled || !hasCameraPermission }">
      <md-icon slot="start">videocam</md-icon>
      <div slot="headline">Default Camera</div>
      <div slot="supporting-text">
        {{
          cameras.length > 0 ? 'Select which camera to use for detection' : 'No cameras available'
        }}
      </div>
      <div slot="end">
        <md-outlined-select
          v-if="cameras.length > 0"
          :disabled="!scannerDetectionEnabled || !hasCameraPermission"
          :value="selectedCameraId"
          class="camera-select-inline"
          @change="(e) => $emit('camera-change', e.target.value)"
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
</template>

<script setup lang="ts">
import { type PropType } from 'vue';

// Presentational settings list for the Camera/Scanner Detection card.
// Holds no state — values come in via props, intent goes out via emits.
const props = defineProps({
  scannerDetectionEnabled: {
    type: Boolean,
    default: false,
  },
  hasCameraPermission: {
    type: Boolean,
    default: false,
  },
  cameras: {
    type: Array as PropType<MediaDeviceInfo[]>,
    default: () => [],
  },
  selectedCameraId: {
    type: String,
    default: '',
  },
});

defineEmits<{
  'update-scanner-detection': [enabled: boolean];
  'camera-change': [deviceId: string];
}>();

// Pure label formatter (no state) — relocated from the parent setup.
function formatCameraLabel(camera: MediaDeviceInfo) {
  if (camera.label) {
    const label = camera.label;
    if (label.length > 20) {
      return label.substring(0, 17) + '...';
    }
    return label;
  }
  return `Camera ${props.cameras.indexOf(camera) + 1}`;
}
</script>

<style scoped>
.camera-select-inline {
  min-width: 180px;
  max-width: 220px;
}

.no-camera-text {
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}
</style>
