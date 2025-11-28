<template>
  <Teleport to="body">
    <Transition name="loading-fade">
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-content">
          <md-circular-progress indeterminate></md-circular-progress>
          <p v-if="message" class="loading-message">{{ message }}</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useLoadingOverlaySetup } from './LoadingOverlay.setup.js';

const { isLoading, message } = useLoadingOverlaySetup();
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-message {
  margin: 0;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  color: var(--md-sys-color-on-surface, #1a1c1e);
  text-align: center;
}

/* Transition animations */
.loading-fade-enter-active {
  transition: opacity 0.2s ease-out;
}

.loading-fade-leave-active {
  transition: opacity 0.3s ease-in;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}
</style>

