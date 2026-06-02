<template>
  <div class="device-card" :class="{ 'current-device': isCurrent }">
    <div class="device-icon-wrapper">
      <md-icon>{{ getDeviceIcon(device.device_type) }}</md-icon>
    </div>
    <div class="device-info">
      <div class="device-name md-typescale-title-medium">
        {{ device.device_name }}
        <md-assist-chip v-if="isCurrent" class="current-badge" has-icon>
          <md-icon slot="icon">check_circle</md-icon>
          Current
        </md-assist-chip>
      </div>
      <div class="device-details md-typescale-body-small">
        <span v-if="device.ip_address" class="detail-item">
          <md-icon>location_on</md-icon>
          {{ device.ip_address }}
        </span>
        <span class="detail-item">
          <md-icon>login</md-icon>
          <template v-if="isCurrent"
            >Logged in {{ formatRelativeTime(device.created_at) }}</template
          >
          <template v-else>{{ formatRelativeTime(device.created_at) }}</template>
        </span>
        <span class="detail-item expiration">
          <md-icon>schedule</md-icon>
          {{ formatExpirationTime(device.expires_at) }}
        </span>
      </div>
    </div>
    <md-icon-button
      v-if="!isCurrent"
      class="revoke-button"
      :disabled="revoking !== null"
      @click="$emit('revoke', device.id)"
    >
      <md-icon>{{ revoking === device.id ? 'hourglass_top' : 'logout' }}</md-icon>
    </md-icon-button>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { Device } from '@dashboard/types/dashboard';

// Presentational device row. State + pure helpers are owned by the parent
// (useDevicesLogic) and passed down — this component holds no state.
defineProps({
  device: {
    type: Object as PropType<Device>,
    required: true,
  },
  isCurrent: {
    type: Boolean,
    default: false,
  },
  revoking: {
    type: [Number, String] as PropType<number | 'all' | null>,
    default: null,
  },
  getDeviceIcon: {
    type: Function as PropType<(deviceType: string) => string>,
    required: true,
  },
  formatRelativeTime: {
    type: Function as PropType<(dateString: string) => string>,
    required: true,
  },
  formatExpirationTime: {
    type: Function as PropType<(dateString: string) => string>,
    required: true,
  },
});

defineEmits<{ revoke: [id: number] }>();
</script>

<style scoped>
.device-card {
  display: flex;
  align-items: flex-start;
  gap: var(--md-sys-spacing-4);
  padding: var(--md-sys-spacing-4);
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-large);
  transition: background-color 0.2s ease;
}

.device-card:hover {
  background: var(--md-sys-color-surface-container);
}

.device-card.current-device {
  background: color-mix(
    in srgb,
    var(--md-sys-color-primary-container) 20%,
    var(--md-sys-color-surface) 80%
  );
  border-color: var(--md-sys-color-primary);
}

.device-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 50%;
  flex-shrink: 0;
}

.device-icon-wrapper md-icon {
  font-size: 24px;
  --md-icon-size: 24px;
  color: var(--md-sys-color-on-surface);
}

.current-device .device-icon-wrapper {
  background: var(--md-sys-color-primary);
}

.current-device .device-icon-wrapper md-icon {
  color: var(--md-sys-color-on-primary);
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  flex-wrap: wrap;
  margin-bottom: var(--md-sys-spacing-2);
}

.current-badge {
  --md-assist-chip-container-color: var(--md-sys-color-primary-container);
  --md-assist-chip-label-text-color: var(--md-sys-color-on-primary-container);
  --md-assist-chip-icon-color: var(--md-sys-color-on-primary-container);
}

.device-details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-sys-spacing-3);
  color: var(--md-sys-color-on-surface-variant);
}

.device-details .detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.device-details .detail-item md-icon {
  font-size: 16px;
  --md-icon-size: 16px;
}

.device-details .detail-item.expiration {
  color: var(--md-sys-color-tertiary);
}

.revoke-button {
  flex-shrink: 0;
  align-self: center;
  --md-icon-button-icon-color: var(--md-sys-color-error);
}

/* DeviceCard responsive adjustments */
@media (max-width: 600px) {
  .device-card {
    flex-direction: column;
    align-items: stretch;
  }

  .device-icon-wrapper {
    align-self: flex-start;
  }
}
</style>
