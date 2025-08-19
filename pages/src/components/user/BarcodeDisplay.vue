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
import {computed, ref} from "vue";

// Material Web Components
import '@material/web/button/elevated-button.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/circular-progress.js';
import '@material/web/progress/linear-progress.js';
import '@material/web/ripple/ripple.js';

// State
const isProcessing = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const barcodeDisplayed = ref(false);
const buttonMessage = ref('PAY / Check-in');
const progressValue = ref(100);
const showProgressBar = ref(false);

// Computed
const buttonIcon = computed(() => {
  if (successMessage.value) return 'check_circle';
  if (errorMessage.value) return 'error';
  if (isProcessing.value) return 'hourglass_empty';
  return 'contactless';
});

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
  successMessage.value = '';
  errorMessage.value = '';
  buttonMessage.value = 'PAY / Check-in';
  progressValue.value = 100;
  showProgressBar.value = false;
}

function startProcessing() {
  resetUI();
  isProcessing.value = true;
  buttonMessage.value = 'Processing...';
}

function showSuccess(message) {
  isProcessing.value = false;
  successMessage.value = message || 'Success';
  buttonMessage.value = message || 'Success';
  barcodeDisplayed.value = true;
  progressValue.value = 100;
  showProgressBar.value = true;

  // Start countdown
  const duration = 10000; // 10 seconds
  const interval = 100; // Update every 100ms
  const decrement = (interval / duration) * 100;
  
  const progressInterval = setInterval(() => {
    progressValue.value -= decrement;
    
    if (progressValue.value <= 0) {
      clearInterval(progressInterval);
      if (barcodeDisplayed.value) {
        resetUI();
      }
    }
  }, interval);
}

function showError(message) {
  isProcessing.value = false;
  errorMessage.value = message || 'Error';
  buttonMessage.value = message || 'Error';

  setTimeout(() => {
    if (errorMessage.value) {
      resetUI();
    }
  }, 4000);
}

function drawPDF417(data) {
  console.log('drawPDF417 called with data:', data);
  
  if (!window.PDF417) {
    console.error('PDF417 library not loaded');
    return;
  }

  try {
    window.PDF417.init(data);
    const barcodeArray = window.PDF417.getBarcodeArray();
    
    console.log('Barcode array:', barcodeArray);
    
    if (!barcodeArray || !barcodeArray['num_cols'] || !barcodeArray['num_rows'] || !barcodeArray['bcode']) {
      console.error('Invalid barcode array generated');
      return;
    }

    // Match the dimensions used in working implementation
    const moduleWidth = 2.5;
    const moduleHeight = 1;

    const canvas = document.createElement('canvas');
    canvas.width = moduleWidth * barcodeArray['num_cols'];
    canvas.height = moduleHeight * barcodeArray['num_rows'];
    canvas.className = 'pdf417-canvas';
    
    // Remove style width/height to prevent scaling issues
    canvas.style.width = '';
    canvas.style.height = '';
    
    console.log('Canvas dimensions:', canvas.width, 'x', canvas.height);

    const barcodeContainer = document.getElementById('barcode-container');
    if (barcodeContainer) {
      barcodeContainer.innerHTML = '';
      barcodeContainer.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      
      // Clear canvas with white background
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw barcode with proper positioning
      ctx.fillStyle = '#000000';
      let y = 0;
      for (let r = 0; r < barcodeArray['num_rows']; r++) {
        let x = 0;
        for (let c = 0; c < barcodeArray['num_cols']; c++) {
          if (barcodeArray['bcode'][r][c] == 1) {
            ctx.fillRect(x, y, moduleWidth, moduleHeight);
          }
          x += moduleWidth;
        }
        y += moduleHeight;
      }
      
      console.log('Barcode drawn successfully');
    } else {
      console.error('Barcode container not found');
    }
  } catch (error) {
    console.error('Error drawing PDF417:', error);
  }
}

// Expose to parent
defineExpose({
  startProcessing,
  showSuccess,
  showError,
  drawPDF417,
  resetUI
});
</script>

<style scoped>
/* Material Design 3 Enhanced Styling */
.barcode-section {
  padding: 24px 16px;
  max-width: 600px;
  margin: 0 auto;
  position: relative;
}

/* Barcode Display Container */
.barcode-display {
  margin-bottom: 32px;
}

/* Material 3 Card Design */
.barcode-card {
  background: var(--md-sys-color-surface-container-high);
  padding: 24px;
  border-radius: var(--md-sys-shape-corner-large);
  box-shadow: var(--md-sys-elevation-level1);
  text-align: center;
  position: relative;
  overflow: hidden;
}

.barcode-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
  var(--md-sys-color-primary) 0%,
  var(--md-sys-color-tertiary) 100%
  );
  opacity: 0.05;
  z-index: 0;
}

.barcode-canvas {
  min-height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  z-index: 1;
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.pdf417-canvas {
  image-rendering: crisp-edges;
  image-rendering: -moz-crisp-edges;
  image-rendering: -webkit-crisp-edges;
  image-rendering: pixelated;
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

.barcode-hint {
  margin-top: 16px;
  font-size: 14px;
  line-height: 20px;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'Roboto', sans-serif;
  letter-spacing: 0.25px;
}

/* Action Button Container */
.action-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* Material 3 Filled Button */
.action-button {
  position: relative;
  width: 100%;
  max-width: 320px;
  height: 56px;
  padding: 0 24px;
  border: none;
  border-radius: var(--md-sys-shape-corner-full);
  background-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.1px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s var(--md-sys-motion-easing-standard);
  box-shadow: var(--md-sys-elevation-level1);
}

.action-button:hover:not(:disabled) {
  box-shadow: var(--md-sys-elevation-level3);
  transform: translateY(-1px);
}

.action-button:active:not(:disabled) {
  box-shadow: var(--md-sys-elevation-level1);
  transform: translateY(0);
}

.action-button:disabled {
  background-color: var(--md-sys-color-on-surface);
  color: var(--md-sys-color-surface);
  opacity: 0.12;
  cursor: not-allowed;
  box-shadow: none;
}

/* Button States */
.action-button.success {
  background-color: var(--md-sys-color-primary);
  animation: success-pulse 0.6s var(--md-sys-motion-easing-emphasized);
}

.action-button.error {
  background-color: var(--md-sys-color-error);
  animation: error-shake 0.4s var(--md-sys-motion-easing-emphasized);
}

.action-button.processing {
  background-color: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

/* Button Content */
.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.button-icon {
  font-size: 18px;
  transition: transform 0.3s var(--md-sys-motion-easing-standard);
}

.action-button:hover:not(:disabled) .button-icon {
  transform: scale(1.1);
}

/* Ripple Effect */
.button-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: currentColor;
  opacity: 0;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.action-button:active:not(:disabled) .button-ripple {
  width: 300%;
  height: 300%;
  opacity: 0.1;
  transition: width 0.6s, height 0.6s, opacity 0.6s;
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-indicator md-circular-progress {
  --md-circular-progress-size: 24px;
  --md-circular-progress-active-indicator-color: var(--md-sys-color-primary);
}

/* Enhanced Animations */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s var(--md-sys-motion-easing-emphasized);
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(-10px);
}

.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s var(--md-sys-motion-easing-standard);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes success-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes error-shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-4px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(4px);
  }
}

/* Progress Bar Styles */
.progress-wrapper {
  margin-top: 20px;
  position: relative;
}

.progress-wrapper md-linear-progress {
  --md-linear-progress-track-height: 8px;
  --md-linear-progress-track-shape: var(--md-sys-shape-corner-full);
  --md-linear-progress-active-indicator-color: var(--md-sys-color-primary);
  --md-linear-progress-track-color: var(--md-sys-color-surface-container-highest);
  width: 100%;
}

.progress-time {
  position: absolute;
  top: -20px;
  right: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'Roboto', sans-serif;
  letter-spacing: 0.4px;
}

/* Responsive Design */
@media (max-width: 600px) {
  .barcode-section {
    padding: 16px 8px;
  }

  .barcode-card {
    padding: 20px 16px;
    border-radius: var(--md-sys-shape-corner-medium);
  }

  .action-button {
    height: 48px;
    font-size: 14px;
  }

  .button-icon {
    font-size: 20px;
  }
}

/* Accessibility */
.action-button:focus-visible {
  outline: 2px solid var(--md-sys-color-on-primary);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .action-button,
  .button-icon,
  .fade-scale-enter-active,
  .fade-scale-leave-active {
    transition: none;
  }

  .action-button.success,
  .action-button.error {
    animation: none;
  }
}
</style>