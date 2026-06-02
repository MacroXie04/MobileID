<template>
  <div class="settings-section md-mt-6">
    <div class="active-barcode-header">
      <md-icon class="active-icon">swap_horiz</md-icon>
      <span class="md-typescale-label-medium">Transfer Dynamic Barcode</span>
    </div>

    <div class="active-barcode-info-wrapper">
      <form class="md-form" @submit.prevent="$emit('submit')">
        <div class="transfer-form md-p-4">
          <div class="form-grid">
            <div>
              <label class="md-typescale-body-small select-label">HTML Content</label>
              <textarea
                :value="html"
                :class="['transfer-textarea', { 'has-error': !!errors.html }]"
                placeholder="Paste the raw HTML from your ID card page..."
                rows="6"
                @input="onInput"
              ></textarea>
              <span v-if="errors.html" class="error-text">{{ errors.html }}</span>
              <span v-else class="helper-text"
                >Paste the complete HTML source of your ID card page. The system will automatically
                extract barcode, name, student ID, and avatar.</span
              >
            </div>
          </div>

          <div class="form-actions md-flex md-gap-3 md-mt-4">
            <md-filled-button :disabled="loading || !html.trim()" type="submit">
              <md-icon slot="icon">{{ loading ? 'hourglass_empty' : 'upload' }}</md-icon>
              {{ loading ? 'Transferring...' : 'Transfer Barcode' }}
            </md-filled-button>
          </div>
        </div>

        <transition name="fade">
          <div v-if="success" class="md-banner md-banner-success md-mx-4 md-mb-4">
            <md-icon>check_circle</md-icon>
            <span class="md-typescale-body-medium">
              {{ successMessage || 'Dynamic barcode transferred successfully!' }}
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
  html: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  success: { type: Boolean, default: false },
  successMessage: { type: String, default: '' },
  error: { type: String, default: '' },
  errors: { type: Object as PropType<Record<string, string>>, default: () => ({}) },
});

const emit = defineEmits<{
  'update:html': [value: string];
  submit: [];
  'clear-error': [];
}>();

function onInput(e: Event) {
  emit('update:html', (e.target as HTMLTextAreaElement).value);
  emit('clear-error');
}
</script>

<style scoped>
/* .transfer-form stays global in BarcodeDashboard.css (shared with the parent's
   static-barcode form). Only the transfer-form-specific rules live here. */
.form-grid {
  display: flex;
  flex-direction: column;
}

.select-label {
  display: block;
  margin-bottom: 8px;
  color: var(--md-sys-color-on-surface-variant);
}

.transfer-textarea {
  width: 100%;
  min-height: 120px;
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

.transfer-textarea:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  border-width: 2px;
}

.transfer-textarea.has-error {
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
