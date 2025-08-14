<template>
  <!-- Barcode + Progress Section -->
  <div id="qrcode" class="barcode-section">
    <div id="qrcode-div" class="barcode-canvas-container" style="display: none;">
      <canvas ref="barcodeCanvas" class="pdf417"></canvas>
    </div>
    <div id="qrcode-code" class="barcode-progress-container" style="display: none;">
      <div class="progress">
        <div
            id="progress-bar"
            class="progress-bar progress-bar-white"
            role="progressbar"
            style="width: 100%;"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue';

import '@material/web/icon/icon';
import '@material/web/button/filled-button.js';

// Template refs
const barcodeCanvas = ref(null);

// Expose canvas ref to parent component
defineExpose({
  barcodeCanvas
});
</script>

<style scoped>
.barcode-section {
  text-align: center;
}

/* Containers are hidden by default using inline styles */

.pdf417 {
  background: #fff;
  image-rendering: pixelated;
  border: 1px solid #dee2e6;
  max-width: 100%;
  height: auto;
  margin: 10px auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: block;
}

#qrcode-code {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-height: 60px;
}

.progress {
  width: 90%;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
  margin: 10px auto 0 auto;
}

.progress-bar-white {
  background-color: #ffc107;
  height: 100%;
}

.progress-container {
  width: 100%;
  max-width: 300px;
  margin: 15px auto 0;
}
</style> 