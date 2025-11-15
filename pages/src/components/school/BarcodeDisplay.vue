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

// CSS
import '@/assets/css/school-merged.css';

// Template refs
const barcodeCanvas = ref(null);

// Expose canvas ref to parent component
defineExpose({
  barcodeCanvas
});
</script>
