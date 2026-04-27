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
        v-show="showBarcode"
        id="qrcode-div"
        class="barcode-canvas-container"
        :aria-hidden="!showBarcode"
      >
        <canvas ref="barcodeCanvas" class="pdf417"></canvas>
      </div>
    </transition>

    <!-- Progress Bar -->
    <transition name="fade">
      <div
        v-show="showBarcode"
        id="qrcode-code"
        class="barcode-progress-container"
        :aria-hidden="!showBarcode"
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

<script setup lang="ts">
import {
  propsDefinition,
  emitsDefinition,
  useMobileIdBarcodeDisplaySetup,
} from './BarcodeDisplay.setup';

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
} = useMobileIdBarcodeDisplaySetup({ props, emit });

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
