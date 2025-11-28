<template>
  <!-- Barcode + Progress Section -->
  <div id="qrcode" class="barcode-section">
    <!-- Hidden video element for background detection -->
    <video
      v-if="scannerDetectionEnabled"
      ref="videoElement"
      class="hidden-video"
      autoplay
      playsinline
      muted
    ></video>
    <canvas v-if="scannerDetectionEnabled" ref="detectionCanvas" class="hidden-canvas"></canvas>

    <!-- Barcode Display -->
    <div
      id="qrcode-div"
      class="barcode-canvas-container"
      :style="{ display: showBarcode ? 'block' : 'none' }"
    >
      <canvas ref="barcodeCanvas" class="pdf417"></canvas>
    </div>

    <!-- Progress Bar -->
    <div
      id="qrcode-code"
      class="barcode-progress-container"
      :style="{ display: showBarcode ? 'block' : 'none' }"
    >
      <div class="progress">
        <div
          id="progress-bar"
          class="progress-bar progress-bar-white"
          role="progressbar"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  propsDefinition,
  emitsDefinition,
  useSchoolBarcodeDisplaySetup,
} from './BarcodeDisplay.setup.js';

const props = defineProps(propsDefinition);
const emit = defineEmits(emitsDefinition);

const {
  barcodeCanvas,
  videoElement,
  detectionCanvas,
  showBarcode,
  progressPercent,
  exposeBindings,
} = useSchoolBarcodeDisplaySetup({ props, emit });

defineExpose(exposeBindings || {});
</script>

<!-- Styles imported via BarcodeDisplay.setup.js from school-merged.css -->
