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
    <transition name="barcode-reveal">
      <div
        id="qrcode-div"
        class="barcode-canvas-container"
        :aria-hidden="String(!showBarcode)"
        v-show="showBarcode"
      >
        <canvas ref="barcodeCanvas" class="pdf417"></canvas>
      </div>
    </transition>

    <!-- Progress Bar -->
    <transition name="fade">
      <div
        id="qrcode-code"
        class="barcode-progress-container"
        :aria-hidden="String(!showBarcode)"
        v-show="showBarcode"
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
    </transition>

    <p v-if="renderError" class="barcode-error" role="status">{{ renderError }}</p>
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
  renderError,
  exposeBindings,
} = useSchoolBarcodeDisplaySetup({ props, emit });

defineExpose(exposeBindings || {});
</script>

<style scoped>
.barcode-error {
  color: #ffd8d8;
  font-size: 0.95rem;
  margin: 12px auto 0;
  max-width: 320px;
}
</style>
