<template>
  <div class="barcode-section">
    <!-- ────── BARCODE DISPLAY ────── -->
    <transition name="fade-scale" @after-leave="clearBarcodeContainer">
      <div v-show="barcodeDisplayed" class="barcode-display">
        <div class="barcode-card">
          <div id="barcode-container" class="barcode-canvas"></div>
          <div class="barcode-hint">{{ successMessage || 'Scan barcode at terminal' }}</div>

          <!-- Progress Bar -->
          <transition name="fade">
            <div v-if="showProgressBar" class="progress-wrapper">
              <md-linear-progress :value="progressValue / 100" />
              <div class="progress-time">{{ Math.ceil(progressValue / 10) }}s</div>
            </div>
          </transition>
        </div>
      </div>
    </transition>

    <!-- ────── BUTTON ────── -->
    <div class="action-wrapper">
      <button
        :class="{
          processing: isProcessing,
          success: successMessage,
          error: errorMessage,
        }"
        :disabled="isProcessing || barcodeDisplayed"
        class="action-button"
        @click="handleGenerate"
      >
        <span class="button-content">
          <md-icon class="button-icon">{{ buttonIcon }}</md-icon>
          <span class="button-label">{{ buttonMessage }}</span>
        </span>
        <span class="button-ripple"></span>
      </button>

      <transition name="fade">
        <div v-if="isProcessing" class="progress-indicator">
          <md-circular-progress indeterminate />
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { emitsDefinition, useUserBarcodeDisplaySetup } from './BarcodeDisplay.setup.js';

const emit = defineEmits(emitsDefinition);

const {
  isProcessing,
  successMessage,
  errorMessage,
  barcodeDisplayed,
  buttonMessage,
  progressValue,
  showProgressBar,
  buttonIcon,
  clearBarcodeContainer,
  handleGenerate,
  exposeBindings,
} = useUserBarcodeDisplaySetup({ emit });

defineExpose(exposeBindings || {});
</script>
