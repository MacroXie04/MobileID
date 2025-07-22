<template>
  <div id="barcode-container" class="text-center mb-3" style="display:none;"></div>

  <div class="button-container">
    <button 
      id="show-barcode-button" 
      ref="mainButton"
      class="btn main-button text-white w-100 py-3 fw-semibold"
      @click="handleGenerate"
      :disabled="isProcessing"
    >
      <div class="progress-overlay" ref="progressOverlay"></div>
      <div class="button-content" ref="buttonContent">
        <span>PAY / Check-in</span>
      </div>
    </button>
  </div>
</template>

<script setup>
import { ref, defineExpose } from 'vue';

// Template refs
const mainButton = ref(null);
const progressOverlay = ref(null);
const buttonContent = ref(null);

// State
const isProcessing = ref(false);

// Emits
const emit = defineEmits(['generate']);

// Handle generate button click
function handleGenerate() {
  if (isProcessing.value) return;
  emit('generate');
}

// UI State Management Functions
function resetUI() {
  isProcessing.value = false;
  if (mainButton.value) {
    mainButton.value.classList.remove('btn-success-custom', 'btn-danger-custom', 'btn-processing-custom', 'pulse-effect');
    mainButton.value.classList.add('main-button');
  }
  if (progressOverlay.value) {
    progressOverlay.value.classList.remove('active');
    progressOverlay.value.style.width = '0%';
  }
  if (buttonContent.value) {
    buttonContent.value.innerHTML = '<span>PAY / Check-in</span>';
  }
  
  // Hide barcode
  const barcodeContainer = document.getElementById('barcode-container');
  if (barcodeContainer) {
    window.$(barcodeContainer).fadeOut(function () {
      barcodeContainer.innerHTML = '';
    });
  }
  console.log('UI reset');
}

function startProcessing() {
  isProcessing.value = true;
  if (mainButton.value) {
    mainButton.value.classList.remove('main-button');
    mainButton.value.classList.add('btn-processing-custom', 'pulse-effect');
  }
  
  if (buttonContent.value) {
    buttonContent.value.innerHTML = `
      <div class="spinner"></div>
      <span>Processing…</span>
    `;
  }
  
  if (progressOverlay.value) {
    progressOverlay.value.classList.add('active');
  }
  
  console.log('Started processing with visual feedback');
}

function showSuccess(message) {
  if (mainButton.value) {
    mainButton.value.classList.remove('btn-processing-custom');
    mainButton.value.classList.add('btn-success-custom', 'pulse-effect');
  }
  
  if (progressOverlay.value) {
    progressOverlay.value.classList.add('active');
  }
  
  if (buttonContent.value) {
    buttonContent.value.innerHTML = `
      <i class="fa-solid fa-check"></i>
      <span>${message || 'Success'}</span>
    `;
  }
  
  // 3秒后停止动画，然后重置
  setTimeout(() => {
    if (progressOverlay.value) {
      progressOverlay.value.classList.remove('active');
      progressOverlay.value.style.width = '100%';
    }
    setTimeout(resetUI, 7000); // 总共10秒
  }, 3000);
}

function showError(message) {
  if (mainButton.value) {
    mainButton.value.classList.remove('btn-processing-custom');
    mainButton.value.classList.add('btn-danger-custom', 'pulse-effect');
  }
  
  if (progressOverlay.value) {
    progressOverlay.value.classList.add('active');
  }
  
  if (buttonContent.value) {
    buttonContent.value.innerHTML = `
      <i class="fa-solid fa-exclamation-triangle"></i>
      <span>${message || 'Error'}</span>
    `;
  }
  
  // 2 sec animation, then reset
  setTimeout(() => {
    if (progressOverlay.value) {
      progressOverlay.value.classList.remove('active');
      progressOverlay.value.style.width = '100%';
    }
    setTimeout(resetUI, 2000);
  }, 2000);
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

    window.$(barcodeContainer).fadeIn();
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
</style> 