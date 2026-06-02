<template>
  <div class="settings-section">
    <div class="active-barcode-header">
      <md-icon class="active-icon">school</md-icon>
      <span class="md-typescale-label-medium">UC Merced Dynamic Barcode</span>
    </div>

    <div class="active-barcode-info-wrapper">
      <form class="md-form" @submit.prevent="$emit('submit')">
        <div class="transfer-form md-p-4">
          <div class="form-grid">
            <md-outlined-text-field
              :value="barcode"
              :error="!!errors.barcode"
              :error-text="errors.barcode"
              class="full-width"
              label="Barcode Number (14 digits)"
              maxlength="14"
              placeholder="Enter 14 digit barcode"
              @input="onBarcodeInput"
            >
              <md-icon slot="leading-icon">qr_code_2</md-icon>
            </md-outlined-text-field>

            <md-outlined-text-field
              :value="name"
              :error="!!errors.name"
              :error-text="errors.name"
              class="full-width md-mt-4"
              label="Full Name"
              placeholder="Enter your full name"
              @input="onNameInput"
            >
              <md-icon slot="leading-icon">person</md-icon>
            </md-outlined-text-field>

            <md-outlined-text-field
              :value="informationId"
              :error="!!errors.information_id"
              :error-text="errors.information_id"
              class="full-width md-mt-4"
              label="Student ID"
              placeholder="Enter your student ID"
              @input="onInformationIdInput"
            >
              <md-icon slot="leading-icon">badge</md-icon>
            </md-outlined-text-field>

            <div class="md-mt-4">
              <label class="md-typescale-body-small select-label">Gender</label>
              <md-outlined-select
                :value="gender"
                class="full-width"
                @change="(e) => $emit('update:gender', e.target.value)"
              >
                <md-select-option value="Male">
                  <div slot="headline">Male</div>
                </md-select-option>
                <md-select-option value="Female">
                  <div slot="headline">Female</div>
                </md-select-option>
                <md-select-option value="Unknow">
                  <div slot="headline">Prefer not to say</div>
                </md-select-option>
              </md-outlined-select>
            </div>

            <div class="md-mt-4">
              <label class="md-typescale-body-small select-label">Avatar (optional)</label>
              <textarea
                :value="avatar"
                :class="['avatar-textarea', { 'has-error': !!errors.avatar }]"
                placeholder="Paste image data URI, e.g. data:image/jpeg;base64,..."
                rows="3"
                @input="onAvatarInput"
              ></textarea>
              <span v-if="errors.avatar" class="error-text">{{ errors.avatar }}</span>
              <span v-else class="helper-text"
                >Paste the full img src value (data:image/jpeg;base64,... or
                data:image/png;base64,...)</span
              >
            </div>
          </div>

          <div class="form-actions md-flex md-gap-3 md-mt-4">
            <md-filled-button :disabled="loading" type="submit">
              <md-icon slot="icon">add</md-icon>
              Create Dynamic Barcode
            </md-filled-button>
          </div>
        </div>

        <transition name="fade">
          <div v-if="success" class="md-banner md-banner-success md-mx-4 md-mb-4">
            <md-icon>check_circle</md-icon>
            <span class="md-typescale-body-medium">
              {{ successMessage || 'Dynamic barcode created successfully!' }}
            </span>
          </div>
        </transition>

        <transition name="fade">
          <div v-if="error" class="md-banner md-banner-error md-mx-4 md-mb-4">
            <md-icon>error</md-icon>
            <span class="md-typescale-body-medium">{{ error }}</span>
          </div>
        </transition>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';

defineProps({
  barcode: { type: String, default: '' },
  name: { type: String, default: '' },
  informationId: { type: String, default: '' },
  gender: { type: String, default: 'Unknow' },
  avatar: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  success: { type: Boolean, default: false },
  successMessage: { type: String, default: '' },
  error: { type: String, default: '' },
  errors: { type: Object as PropType<Record<string, string>>, default: () => ({}) },
});

const emit = defineEmits<{
  'update:barcode': [value: string];
  'update:name': [value: string];
  'update:informationId': [value: string];
  'update:gender': [value: string];
  'update:avatar': [value: string];
  submit: [];
  'clear-error': [field: string];
}>();

// Each text input forwards its value via the matching update:* model event and
// clears that field's error. The events are emitted explicitly (rather than via a
// union variable) so defineEmits' typed overloads resolve.
function eventValue(e: Event): string {
  return (e.target as HTMLInputElement | HTMLTextAreaElement).value;
}

function onBarcodeInput(e: Event) {
  emit('update:barcode', eventValue(e));
  emit('clear-error', 'barcode');
}

function onNameInput(e: Event) {
  emit('update:name', eventValue(e));
  emit('clear-error', 'name');
}

function onInformationIdInput(e: Event) {
  emit('update:informationId', eventValue(e));
  emit('clear-error', 'information_id');
}

function onAvatarInput(e: Event) {
  emit('update:avatar', eventValue(e));
  emit('clear-error', 'avatar');
}
</script>

<style scoped>
/* .transfer-form / .full-width stay global in BarcodeDashboard.css (shared with the
   parent's static-barcode form). Only the dynamic-form-specific rules live here. */
.form-grid {
  display: flex;
  flex-direction: column;
}

.select-label {
  display: block;
  margin-bottom: 8px;
  color: var(--md-sys-color-on-surface-variant);
}

.avatar-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px 16px;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: var(--md-sys-shape-corner-small);
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  resize: vertical;
  transition: border-color 0.2s ease;
}

.avatar-textarea:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  border-width: 2px;
}

.avatar-textarea.has-error {
  border-color: var(--md-sys-color-error);
}

.helper-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.error-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--md-sys-color-error);
}
</style>
