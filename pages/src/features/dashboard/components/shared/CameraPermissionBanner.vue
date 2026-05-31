<template>
  <div class="permission-banner">
    <div class="permission-banner-icon">
      <md-icon>videocam_off</md-icon>
    </div>
    <div class="permission-banner-content">
      <span class="permission-banner-title">{{ title }}</span>
      <span class="permission-banner-desc">{{ description }}</span>
    </div>
    <md-filled-tonal-button :disabled="isRequesting" @click="$emit('request')">
      <md-icon slot="icon">{{ isRequesting ? 'hourglass_empty' : 'videocam' }}</md-icon>
      {{ isRequesting ? 'Requesting...' : 'Allow' }}
    </md-filled-tonal-button>
  </div>
</template>

<script setup lang="ts">
// Shared camera-permission prompt used by AddBarcodeCard and CameraSettingsCard.
defineProps({
  title: { type: String, default: 'Camera Permission Required' },
  description: {
    type: String,
    default: 'Enable camera access to scan barcodes with camera',
  },
  isRequesting: { type: Boolean, default: false },
});

defineEmits<{ request: [] }>();
</script>
