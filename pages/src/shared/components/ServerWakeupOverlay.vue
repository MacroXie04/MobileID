<template>
  <Teleport to="body">
    <Transition name="wakeup-fade">
      <div v-if="isWakingUp" class="server-wakeup-overlay">
        <div class="wakeup-content">
          <!-- Google Cloud Logo -->
          <div class="wakeup-icon-container">
            <svg class="google-cloud-logo" viewBox="0 0 256 206" xmlns="http://www.w3.org/2000/svg">
              <!-- Google Cloud hexagon logo -->
              <path
                d="M170.252 56.819l22.253-22.253 1.483-9.37C153.437-11.677 88.976-7.496 52.42 33.92 42.267 45.427 34.39 58.837 29.253 73.37l7.96-1.107 44.505-7.34 3.436-3.513c19.795-21.742 52.145-24.791 75.098-6.59z"
                fill="#EA4335"
              />
              <path
                d="M224.205 73.918a100.249 100.249 0 00-30.217-48.722l-31.232 31.232a55.515 55.515 0 0120.379 44.037v5.544c15.35 0 27.797 12.446 27.797 27.796 0 15.352-12.446 27.573-27.797 27.573h-55.671l-5.544 5.621v33.339l5.544 5.544h55.67c39.93.311 72.553-31.494 72.865-71.424a72.303 72.303 0 00-31.794-60.54z"
                fill="#4285F4"
              />
              <path
                d="M71.87 205.796h55.593V161.29H71.87a27.275 27.275 0 01-11.399-2.498l-7.882 2.42-22.409 22.253-1.952 7.574c12.567 9.489 27.9 14.825 43.642 14.757z"
                fill="#34A853"
              />
              <path
                d="M71.87 61.026C31.94 61.259-.237 93.74.001 133.669a72.301 72.301 0 0028.227 56.893l32.243-32.243c-14.823-6.741-21.386-24.178-14.645-39 6.74-14.823 24.178-21.386 39-14.645a27.798 27.798 0 0114.645 14.645l32.243-32.243a72.224 72.224 0 00-59.844-25.05z"
                fill="#FBBC05"
              />
            </svg>
          </div>

          <!-- Status Text -->
          <h2 class="wakeup-title">Connecting to Google Cloud Run</h2>

          <!-- Google-style progress bar -->
          <div class="google-progress-container">
            <div class="google-progress-bar"></div>
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
