<template>
  <section class="dashboard-card passkeys-card">
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>passkey</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-title-medium md-m-0">Passkeys</h2>
      </div>
      <md-filled-button
        class="add-passkey-btn"
        :disabled="!passkeySupported || passkeyLoading"
        @click="handleRegister"
      >
        <md-circular-progress v-if="passkeyLoading" indeterminate></md-circular-progress>
        <md-icon v-else slot="icon">add_circle</md-icon>
        {{ passkeyLoading ? 'Registering...' : registerCta }}
      </md-filled-button>
    </div>

    <transition name="slide-up">
      <div
        v-if="passkeySuccess"
        class="md-banner md-banner-success passkey-banner"
        @click="clearPasskeySuccess"
      >
        <md-icon>check_circle</md-icon>
        <span class="md-typescale-body-medium">{{ passkeySuccess }}</span>
      </div>
    </transition>

    <transition name="slide-up">
      <div
        v-if="passkeyError"
        class="md-banner md-banner-error passkey-banner"
        @click="clearPasskeyError"
      >
        <md-icon>error_outline</md-icon>
        <span class="md-typescale-body-medium">{{ passkeyError }}</span>
      </div>
    </transition>

    <div class="passkeys-body">
      <div v-if="!passkeySupported" class="info-banner">
        <md-icon>info</md-icon>
        <div class="info-content">
          <p class="md-typescale-title-small md-m-0">Passkeys not supported</p>
          <p class="md-typescale-body-medium md-m-0">
            This browser or device does not support WebAuthn passkeys. Please try a supported
            browser (Chrome, Edge, Safari, or Firefox with WebAuthn) on a device with biometrics or
            security key support.
          </p>
        </div>
      </div>

      <div v-else class="passkeys-info">
        <div class="info-banner">
          <md-icon>shield</md-icon>
          <div class="info-content">
            <p class="md-typescale-title-small md-m-0">Why use passkeys?</p>
            <p class="md-typescale-body-medium md-m-0">
              Passkeys let you sign in with biometrics or a security key—no passwords to remember.
              You can create multiple passkeys across your trusted devices.
            </p>
          </div>
        </div>

        <div class="passkey-status">
          <md-assist-chip :disabled="true" :selected="hasPasskey" class="status-chip">
            <md-icon slot="icon">{{ hasPasskey ? 'check_circle' : 'info' }}</md-icon>
            {{ hasPasskey ? 'Passkey registered' : 'No passkey on file' }}
          </md-assist-chip>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { usePasskeyRegister } from '@dashboard/composables/usePasskeyRegister.js';

const {
  passkeySupported,
  passkeyLoading,
  passkeyError,
  passkeySuccess,
  hasPasskey,
  fetchPasskeyStatus,
  registerPasskey,
  clearPasskeyError,
  clearPasskeySuccess,
} = usePasskeyRegister();

const registerCta = computed(() => (hasPasskey.value ? 'Replace Passkey' : 'Add Passkey'));

async function handleRegister() {
  const ok = await registerPasskey();
  if (ok) {
    await fetchPasskeyStatus();
  }
}
</script>
