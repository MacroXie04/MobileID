<template>
  <div class="barcode-limit-section">
    <div class="limit-row">
      <div class="limit-label">
        <md-icon>event</md-icon>
        <span>Daily Limit</span>
      </div>
      <div class="limit-toggle">
        <span class="toggle-label">{{
          Number(barcode.daily_usage_limit || 0) === 0
            ? 'Unlimited'
            : barcode.daily_usage_limit + '/day'
        }}</span>
        <md-switch
          :selected="Number(barcode.daily_usage_limit || 0) === 0"
          @change="(e) => $emit('toggle-unlimited-switch', barcode, e)"
        ></md-switch>
      </div>
    </div>
    <transition name="expand">
      <div v-if="Number(barcode.daily_usage_limit || 0) !== 0" class="limit-controls-row">
        <md-icon-button @click="$emit('decrement-limit', barcode)">
          <md-icon>remove</md-icon>
        </md-icon-button>
        <md-outlined-text-field
          :value="barcode.daily_usage_limit || 0"
          class="limit-input"
          min="1"
          type="number"
          @input="(e) => $emit('update-limit', barcode, e.target.value)"
        ></md-outlined-text-field>
        <md-icon-button @click="$emit('increment-limit', barcode)">
          <md-icon>add</md-icon>
        </md-icon-button>
        <div class="limit-presets">
          <md-assist-chip @click="$emit('apply-limit-preset', barcode, 10)">10</md-assist-chip>
          <md-assist-chip @click="$emit('apply-limit-preset', barcode, 15)">15</md-assist-chip>
          <md-assist-chip @click="$emit('apply-limit-preset', barcode, 20)">20</md-assist-chip>
        </div>
        <md-circular-progress v-if="updating" indeterminate></md-circular-progress>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { Barcode } from '@barcode';

// Presentational daily-limit controls for a single barcode. State lives in the parent.
defineProps({
  barcode: { type: Object as PropType<Barcode>, required: true },
  updating: { type: Boolean, default: false },
});

defineEmits<{
  'update-limit': [barcode: Barcode, value: string];
  'increment-limit': [barcode: Barcode];
  'decrement-limit': [barcode: Barcode];
  'toggle-unlimited-switch': [barcode: Barcode, event: Event];
  'apply-limit-preset': [barcode: Barcode, value: number];
}>();
</script>

<style scoped>
.barcode-limit-section {
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
  padding: var(--md-sys-spacing-3);
}

.limit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.limit-label {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  font-size: var(--md-sys-typescale-label-large-size);
  font-weight: var(--md-sys-typescale-label-large-weight);
  color: var(--md-sys-color-on-surface);
}

.limit-label md-icon {
  font-size: 18px;
  --md-icon-size: 18px;
  color: var(--md-sys-color-primary);
}

.limit-toggle {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
}

.toggle-label {
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}

.limit-controls-row {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  margin-top: var(--md-sys-spacing-3);
  padding-top: var(--md-sys-spacing-3);
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.limit-controls-row .limit-input {
  width: 100px;
  --md-outlined-text-field-container-shape: var(--md-sys-shape-corner-small);
}

.limit-presets {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-1);
  margin-left: auto;
}

.limit-presets md-assist-chip {
  --md-assist-chip-container-shape: var(--md-sys-shape-corner-small);
}

@media (max-width: 600px) {
  .limit-controls-row {
    flex-wrap: wrap;
  }

  .limit-presets {
    width: 100%;
    margin-left: 0;
    margin-top: var(--md-sys-spacing-2);
    justify-content: center;
  }
}
</style>
