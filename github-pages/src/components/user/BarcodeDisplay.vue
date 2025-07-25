<template>
  <div class="barcode-display-section">
    <transition name="barcode" @after-leave="clearBarcodeContainer">
      <div id="barcode-container" class="barcode-canvas-container" v-show="barcodeDisplayed" style="margin-bottom: 16px;"></div>
    </transition>
    <div class="button-container">
      <md-filled-button 
        :class="['main-button', ...additionalButtonClasses]"
        @click="handleGenerate"
        :disabled="isProcessing"
      >
        <md-icon slot="icon">qr_code</md-icon>
        {{ buttonMessage }}
      </md-filled-button>
      <md-linear-progress v-if="barcodeDisplayed" :value="remainingTime / 100" style="margin-top: 8px;"></md-linear-progress>
      <div v-if="isProcessing" class="progress-overlay active"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineExpose } from "vue";

import '@material/web/button/filled-button.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/linear-progress.js';

// Template refs
const mainButton = ref(null);
const progressOverlay = ref(null);
const buttonContent = ref(null);
const buttonMessage = ref('PAY / Check-in');
const additionalButtonClasses = ref([]);

// State
const isProcessing = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const barcodeDisplayed = ref(false);
const remainingTime = ref(100);
let timerInterval = null;

// Emits
const emit = defineEmits(['generate']);

// Handle generate button click
function handleGenerate() {
  if (isProcessing.value) return;
  emit('generate');
}

// UI State Management Functions
function clearBarcodeContainer() {
  const barcodeContainer = document.getElementById('barcode-container');
  if (barcodeContainer) {
    barcodeContainer.innerHTML = '';
  }
}

function resetUI() {
  isProcessing.value = false;
  barcodeDisplayed.value = false;
  buttonMessage.value = 'PAY / Check-in';
  additionalButtonClasses.value = [];
  clearInterval(timerInterval);
  console.log('UI reset');
}

function startProcessing() {
  isProcessing.value = true;
  additionalButtonClasses.value = ['btn-processing-custom', 'pulse-effect'];
  buttonMessage.value = 'Processing...';
  console.log('Started processing');
}

function showSuccess(message) {
  buttonMessage.value = message || 'Success';
  additionalButtonClasses.value = ['btn-success-custom', 'pulse-effect'];
  barcodeDisplayed.value = true;
  remainingTime.value = 100;
  timerInterval = setInterval(() => {
    remainingTime.value -= 1;
    if (remainingTime.value <= 0) {
      clearInterval(timerInterval);
      resetUI();
    }
  }, 100);  // 10 seconds total
}

function showError(message) {
  buttonMessage.value = message || 'Error';
  additionalButtonClasses.value = ['btn-danger-custom', 'pulse-effect'];
  setTimeout(() => {
    resetUI();
  }, 4000);
}

function drawPDF417(data) {
  if (!window.PDF417) {
    console.error('PDF417 library not loaded');
    return;
  }
  
  window.PDF417.init(data);
  const barcode = window.PDF417.getBarcodeArray();

  const bw = 2.5;
  const bh = 1;

  const canvas = document.createElement('canvas');
  canvas.width = bw * barcode['num_cols'];
  canvas.height = bh * barcode['num_rows'];
  canvas.className = 'pdf417';

  const barcodeContainer = document.getElementById('barcode-container');
  if (barcodeContainer) {
    barcodeContainer.innerHTML = '';
    barcodeContainer.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    for (let r = 0; r < barcode['num_rows']; ++r) {
      for (let c = 0; c < barcode['num_cols']; ++c) {
        if (barcode['bcode'][r][c] == 1) {
          ctx.fillStyle = '#000';
          ctx.fillRect(c * bw, r * bh, bw, bh);
        }
      }
    }
  }
}

// Expose functions to parent
defineExpose({
  startProcessing,
  showSuccess,
  showError,
  drawPDF417,
  resetUI
});
</script>

<style scoped>
/* Component-specific styles are handled by imported CSS */
.success-message {
  background-color: var(--md-sys-color-primary);
  color: white;
  padding: 8px;
  margin-top: 8px;
  border-radius: 4px;
}
.error-message {
  background-color: var(--md-sys-color-error);
  color: white;
  padding: 8px;
  margin-top: 8px;
  border-radius: 4px;
}
.barcode-enter-active, .barcode-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.barcode-enter-from, .barcode-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
.barcode-enter-to, .barcode-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style> 