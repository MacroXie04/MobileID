<template>
  <article
    :class="{
      'is-active': isActive,
      'is-shared': !barcode.is_owned_by_current_user,
    }"
    class="barcode-card"
  >
    <!-- Card Header: Icon + Title + Status -->
    <div class="barcode-card-header">
      <div class="barcode-type-icon">
        <md-icon aria-hidden="true">{{ iconForType(barcode.barcode_type) }}</md-icon>
      </div>
      <div class="barcode-header-content">
        <div class="barcode-title-row">
          <h3 class="barcode-title">{{ getBarcodeDisplayTitle(barcode.barcode_type) }}</h3>
          <span class="barcode-type-label">{{ getBarcodeTypeLabel(barcode.barcode_type) }}</span>
        </div>
        <p class="barcode-id">{{ getBarcodeDisplayId(barcode) }}</p>
      </div>
      <!-- Active Badge -->
      <div v-if="isActive" class="active-badge">
        <md-icon>check_circle</md-icon>
        <span>Active</span>
      </div>
    </div>

    <!-- Owner & Share Info -->
    <div
      v-if="
        barcode.owner ||
        !barcode.is_owned_by_current_user ||
        (barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon)
      "
      class="barcode-meta"
    >
      <md-assist-chip v-if="barcode.owner" has-icon>
        <md-icon slot="icon">person</md-icon>
        {{ barcode.owner }}
      </md-assist-chip>
      <md-assist-chip v-if="!barcode.is_owned_by_current_user" has-icon>
        <md-icon slot="icon">group</md-icon>
        Shared with you
      </md-assist-chip>
      <md-assist-chip
        v-if="barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon"
        :title="getProfileTooltip(barcode)"
        has-icon
      >
        <md-icon slot="icon">{{
          barcode.profile_info?.has_avatar ? 'account_circle' : 'badge'
        }}</md-icon>
        {{ getProfileLabel(barcode) }}
      </md-assist-chip>
    </div>

    <!-- Usage Stats -->
    <div class="barcode-stats-row">
      <div class="stat-item">
        <md-icon>trending_up</md-icon>
        <span class="stat-value">{{ barcode.usage_count || 0 }}</span>
        <span class="stat-label">scans</span>
      </div>
      <div v-if="barcode.last_used" class="stat-item">
        <md-icon>schedule</md-icon>
        <span class="stat-value">{{ formatRelativeTime(barcode.last_used) }}</span>
      </div>
      <div v-if="barcode.usage_stats" class="stat-item">
        <md-icon>today</md-icon>
        <span class="stat-value">{{ barcode.usage_stats.daily_used }}</span>
        <span class="stat-label">today</span>
      </div>
    </div>

    <!-- Daily Limit Section -->
    <BarcodeDailyLimitControl
      v-if="barcode.is_owned_by_current_user"
      :barcode="barcode"
      :updating="updating"
      @update-limit="(b, value) => $emit('update-limit', b, value)"
      @increment-limit="(b) => $emit('increment-limit', b)"
      @decrement-limit="(b) => $emit('decrement-limit', b)"
      @toggle-unlimited-switch="(b, e) => $emit('toggle-unlimited-switch', b, e)"
      @apply-limit-preset="(b, value) => $emit('apply-limit-preset', b, value)"
    />

    <!-- Card Actions -->
    <div class="barcode-card-actions">
      <md-filled-tonal-button
        v-if="!isActive"
        :disabled="pullEnabled"
        :title="pullEnabled ? 'Disabled when auto-pull is enabled' : 'Set as active barcode'"
        @click="$emit('set-active', barcode)"
      >
        <md-icon slot="icon">check_circle</md-icon>
        Set Active
      </md-filled-tonal-button>
      <md-outlined-button
        v-if="barcode.is_owned_by_current_user"
        @click="$emit('toggle-share', barcode)"
      >
        <md-icon slot="icon">{{ barcode.share_with_others ? 'lock_open' : 'lock' }}</md-icon>
        {{ barcode.share_with_others ? 'Public' : 'Private' }}
      </md-outlined-button>
      <md-icon-button v-if="barcode.is_owned_by_current_user" @click="$emit('delete', barcode)">
        <md-icon>delete</md-icon>
      </md-icon-button>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { Barcode } from '@barcode';
import { useBarcodesListLogic } from '@dashboard/composables/useBarcodesListLogic';
import BarcodeDailyLimitControl from './BarcodeDailyLimitControl.vue';

// Presentational single-barcode card. State lives in the parent; display helpers
// are pure functions safe to call per-item.
defineProps({
  barcode: { type: Object as PropType<Barcode>, required: true },
  isActive: { type: Boolean, default: false },
  pullEnabled: { type: Boolean, default: false },
  updating: { type: Boolean, default: false },
});

defineEmits<{
  'set-active': [barcode: Barcode];
  'toggle-share': [barcode: Barcode];
  delete: [barcode: Barcode];
  'update-limit': [barcode: Barcode, value: string];
  'increment-limit': [barcode: Barcode];
  'decrement-limit': [barcode: Barcode];
  'toggle-unlimited-switch': [barcode: Barcode, event: Event];
  'apply-limit-preset': [barcode: Barcode, value: number];
}>();

const {
  iconForType,
  getBarcodeDisplayTitle,
  getBarcodeTypeLabel,
  getProfileLabel,
  getProfileTooltip,
  getBarcodeDisplayId,
  formatRelativeTime,
} = useBarcodesListLogic();
</script>

<style scoped>
.barcode-card {
  background: var(--md-sys-color-surface);
  border-radius: var(--md-sys-shape-corner-large);
  border: 1px solid var(--md-sys-color-outline-variant);
  padding: var(--md-sys-spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-3);
  transition: all 0.2s ease;
}

.barcode-card:hover {
  box-shadow: var(--md-elevation-1);
}

.barcode-card.is-active {
  border-color: var(--md-sys-color-primary);
  background: color-mix(
    in srgb,
    var(--md-sys-color-primary-container) 25%,
    var(--md-sys-color-surface) 75%
  );
}

.barcode-card.is-active .barcode-type-icon {
  background: var(--md-sys-color-primary);
}

.barcode-card.is-active .barcode-type-icon md-icon {
  color: var(--md-sys-color-on-primary);
}

.barcode-card.is-shared {
  background: var(--md-sys-color-surface-container-low);
}

/* Card Header */
.barcode-card-header {
  display: flex;
  align-items: flex-start;
  gap: var(--md-sys-spacing-3);
}

.barcode-type-icon {
  width: 48px;
  height: 48px;
  background: var(--md-sys-color-primary-container);
  border-radius: var(--md-sys-shape-corner-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.barcode-type-icon md-icon {
  font-size: 24px;
  --md-icon-size: 24px;
  color: var(--md-sys-color-on-primary-container);
}

.barcode-header-content {
  flex: 1;
  min-width: 0;
}

.barcode-title-row {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  flex-wrap: wrap;
}

.barcode-title {
  margin: 0;
  font-size: var(--md-sys-typescale-title-medium-size);
  font-weight: var(--md-sys-typescale-title-medium-weight);
  color: var(--md-sys-color-on-surface);
}

.barcode-type-label {
  font-size: var(--md-sys-typescale-label-small-size);
  font-weight: 500;
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  padding: 2px 8px;
  border-radius: 4px;
}

.barcode-id {
  margin: 4px 0 0;
  font-family: 'Roboto Mono', monospace;
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}

.active-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.active-badge md-icon {
  font-size: 14px;
  --md-icon-size: 14px;
}

/* Barcode Meta (Owner, Shared, Profile) */
.barcode-meta {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  flex-wrap: wrap;
}

/* Stats Row */
.barcode-stats-row {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-4);
  padding: var(--md-sys-spacing-3);
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-body-small-size);
}

.stat-item md-icon {
  font-size: 16px;
  --md-icon-size: 16px;
  color: var(--md-sys-color-primary);
}

.stat-value {
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.stat-label {
  color: var(--md-sys-color-on-surface-variant);
}

/* Card Actions */
.barcode-card-actions {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  padding-top: var(--md-sys-spacing-3);
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

@media (max-width: 600px) {
  .barcode-card-header {
    flex-wrap: wrap;
  }

  .active-badge {
    order: -1;
    width: 100%;
    justify-content: center;
    margin-bottom: var(--md-sys-spacing-2);
  }

  .barcode-stats-row {
    flex-wrap: wrap;
    gap: var(--md-sys-spacing-3);
  }

  .barcode-card-actions {
    flex-wrap: wrap;
  }

  .barcode-card-actions md-filled-tonal-button,
  .barcode-card-actions md-outlined-button {
    flex: 1;
  }
}

@media (max-width: 904px) {
  .barcode-type-icon {
    display: none;
  }
}
</style>
