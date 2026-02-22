<template>
  <Teleport to="body">
    <Transition name="wakeup-fade">
      <div v-if="isWakingUp" class="server-wakeup-overlay">
        <div class="wakeup-content">
          <!-- Loading Icon -->
          <div class="wakeup-icon-container">
            <md-icon class="wakeup-cloud-icon">cloud</md-icon>
          </div>

          <!-- Status Text -->
          <h2 class="wakeup-title">Connecting to Server</h2>

          <!-- AWS-style progress bar -->
          <div class="aws-progress-container">
            <div class="aws-progress-bar"></div>
          </div>

          <!-- Elapsed Time -->
          <p class="wakeup-elapsed">{{ formatElapsedTime(elapsedMs) }}</p>

          <!-- Error Message -->
          <Transition name="error-fade">
            <div v-if="errorMessage" class="wakeup-error">
              <md-icon>error_outline</md-icon>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useServerWakeupOverlaySetup } from './ServerWakeupOverlay.setup.js';

const { isWakingUp, elapsedMs, errorMessage, formatElapsedTime } = useServerWakeupOverlaySetup();
</script>
