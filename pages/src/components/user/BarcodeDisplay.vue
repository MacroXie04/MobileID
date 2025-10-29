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
          error: errorMessage
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
          <md-circular-progress indeterminate/>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import '@material/web/button/elevated-button.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/circular-progress.js';
import '@material/web/progress/linear-progress.js';
import '@material/web/ripple/ripple.js';

import {useBarcodeDisplay} from '@/composables/useBarcodeDisplay.js';
import {usePdf417} from '@/composables/usePdf417.js';

// CSS
import '@/assets/css/user-merged.css';

// Emits
const emit = defineEmits(['generate']);

// Use composables
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
  resetUI,
  startProcessing,
  showSuccess,
  showError
} = useBarcodeDisplay();

const {drawPdf417ToContainer} = usePdf417();

// Handle generate button click
function handleGenerate() {
  if (isProcessing.value) return;
  emit('generate');
}

// Draw PDF417 barcode
function drawPDF417(data) {
  drawPdf417ToContainer('barcode-container', data, {
    moduleWidth: 2.5,
    moduleHeight: 1
  });
}

// Expose to parent
defineExpose({
  startProcessing,
  showSuccess,
  showError,
  drawPDF417,
  resetUI
