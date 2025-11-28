<template>
  <section ref="addSectionLocal" class="dashboard-card">
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>add_circle</md-icon>
      </div>
      <h2 class="md-typescale-headline-small">Add New Barcode</h2>
    </div>

    <!-- Transfer Barcode (moved from TransferBarcode.vue) -->
    <div class="md-mb-6">
      <div class="subsection-header md-flex md-items-center md-gap-3 md-mb-4">
        <md-icon>cookie</md-icon>
        <h3 class="md-typescale-title-medium md-m-0">Transfer Barcode</h3>
        <transition name="fade">
          <div
            v-if="transferLoading"
            class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto"
          >
            <md-circular-progress indeterminate></md-circular-progress>
            <span class="md-typescale-body-small">Collecting Data from URL...</span>
          </div>
        </transition>
      </div>

      <div class="settings-content md-flex md-flex-column md-gap-4">
        <md-outlined-text-field
          v-model="transferCookie"
          :error="!!transferErrors.cookie"
          :error-text="transferErrors.cookie"
          label="Barcode Cookie"
          placeholder="Paste your Barcode cookies here"
          @input="clearTransferError('cookie')"
        >
          <md-icon slot="leading-icon">cookie</md-icon>
        </md-outlined-text-field>

        <div class="md-flex md-items-center md-gap-2">
          <md-icon>link</md-icon>
          <span class="md-typescale-body-medium">ID Server:</span>
          <code class="md-typescale-body-medium">https://icatcard.ucmerced.edu/mobileid/</code>
        </div>

        <div class="form-actions md-flex md-gap-3 md-flex-wrap">
          <md-filled-button
            :disabled="transferLoading || !transferCookie.trim()"
            @click="requestTransferCode"
          >
            <md-icon slot="icon">sync_alt</md-icon>
            Request Transfer
          </md-filled-button>
        </div>

        <transition name="fade">
          <div v-if="transferSuccess" class="md-banner md-banner-success">
            <md-icon>check_circle</md-icon>
            <span class="md-typescale-body-medium">
              {{ transferSuccessMessage || 'Barcode data stored successfully!' }}
            </span>
          </div>
        </transition>

        <transition name="fade">
          <div v-if="transferError" class="md-banner md-banner-error">
            <md-icon>error</md-icon>
            <span class="md-typescale-body-medium">{{ transferError }}</span>
          </div>
        </transition>
      </div>
    </div>

    <form class="md-form" @submit.prevent="addBarcode">
      <div class="form-content md-flex md-flex-column md-gap-4">
        <md-outlined-text-field
          v-model="newBarcode"
          :error="!!errors.newBarcode"
          :error-text="errors.newBarcode"
          label="Barcode Number"
          placeholder="Enter or scan barcode"
          @input="clearError('newBarcode')"
        >
          <md-icon slot="leading-icon">pin</md-icon>
        </md-outlined-text-field>

        <div class="form-actions md-flex md-gap-3 md-flex-wrap">
          <md-outlined-button type="button" @click="toggleScanner">
            <md-icon slot="icon">{{ showScanner ? 'videocam_off' : 'qr_code_scanner' }}</md-icon>
            {{ showScanner ? 'Close Scanner' : 'Scan with Camera' }}
          </md-outlined-button>

          <md-filled-button :disabled="!newBarcode.trim()" type="submit">
            <md-icon slot="icon">add</md-icon>
            Add Barcode
          </md-filled-button>
        </div>
      </div>

      <transition name="expand">
        <div
          v-if="showScanner"
          class="scanner-container md-card md-card-filled md-rounded-lg md-p-5 md-mt-6"
        >
          <div class="scanner-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>camera</md-icon>
            <span class="md-typescale-title-medium">Barcode Scanner</span>
            <md-outlined-select
              v-if="cameras.length > 1"
              v-model="selectedCameraId"
              class="camera-select md-ml-auto"
            >
              <md-select-option
                v-for="device in cameras"
                :key="device.deviceId"
                :value="device.deviceId"
              >
                <div slot="headline">{{ device.label }}</div>
              </md-select-option>
            </md-outlined-select>
          </div>

          <div class="scanner-viewport md-rounded-lg">
            <video ref="videoRef" autoplay muted playsinline webkit-playsinline></video>
            <div class="scanner-overlay">
              <div class="scanner-frame"></div>
            </div>
          </div>

          <div class="scanner-status md-text-center md-mt-4">
            <md-linear-progress v-if="scanning" indeterminate></md-linear-progress>
            <p class="md-typescale-body-small md-mt-2">{{ scannerStatus }}</p>
          </div>
        </div>
      </transition>
    </form>
  </section>
</template>

<script setup>
import {
  emitsDefinition,
  propsDefinition,
  useAddBarcodeCardSetup,
} from './AddBarcodeCard.setup.js';

defineProps(propsDefinition);
const emit = defineEmits(emitsDefinition);

const {
  addSectionLocal,
  newBarcode,
  errors,
  transferCookie,
  transferLoading,
  transferSuccess,
  transferSuccessMessage,
  transferError,
  transferErrors,
  showScanner,
  scanning,
  scannerStatus,
  videoRef,
  cameras,
  selectedCameraId,
  toggleScanner,
  clearError,
  addBarcode,
  clearTransferError,
  requestTransferCode,
} = useAddBarcodeCardSetup({ emit });
</script>
