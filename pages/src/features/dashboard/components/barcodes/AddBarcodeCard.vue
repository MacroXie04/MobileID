<template>
  <section ref="addSectionLocal" class="dashboard-card md-mb-6">
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>add_circle</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small">Add New Barcode</h2>
      </div>
      <transition name="fade">
        <div
          v-if="dynamicLoading || transferLoading"
          class="save-indicator md-flex md-items-center md-gap-2"
        >
          <md-circular-progress indeterminate></md-circular-progress>
          <span class="md-typescale-body-small">Processing...</span>
        </div>
      </transition>
    </div>

    <div class="settings-content">
      <!-- Camera Permission Banner -->
      <CameraPermissionBanner
        v-if="!hasCameraPermission"
        :is-requesting="isRequestingPermission"
        @request="requestCameraPermission"
      />

      <!-- Static Barcode Section -->
      <div class="settings-section md-mb-6">
        <div class="active-barcode-header">
          <md-icon class="active-icon">edit</md-icon>
          <span class="md-typescale-label-medium">Add Static Barcode</span>
        </div>

        <div class="active-barcode-info-wrapper">
          <form class="md-form" @submit.prevent="addBarcode">
            <div class="transfer-form md-p-4">
              <md-outlined-text-field
                v-model="newBarcode"
                :error="!!errors.newBarcode"
                :error-text="errors.newBarcode"
                class="full-width"
                label="Barcode Number"
                placeholder="Enter or scan barcode"
                @input="clearError('newBarcode')"
              >
                <md-icon slot="leading-icon">pin</md-icon>
              </md-outlined-text-field>

              <div class="form-actions md-flex md-gap-3 md-mt-4 md-flex-wrap">
                <md-outlined-button
                  :disabled="!hasCameraPermission"
                  type="button"
                  @click="toggleScanner"
                >
                  <md-icon slot="icon">{{
                    showScanner ? 'videocam_off' : 'qr_code_scanner'
                  }}</md-icon>
                  {{ showScanner ? 'Close Scanner' : 'Scan with Camera' }}
                </md-outlined-button>

                <md-filled-button :disabled="!newBarcode.trim()" type="submit">
                  <md-icon slot="icon">add</md-icon>
                  Add Barcode
                </md-filled-button>
              </div>
            </div>

            <transition name="expand">
              <div v-if="showScanner" class="scanner-section md-p-4">
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
        </div>
      </div>

      <!-- UC Merced Dynamic Barcode Section -->
      <DynamicBarcodeForm
        v-model:barcode="dynamicBarcode"
        v-model:name="dynamicName"
        v-model:information-id="dynamicInformationId"
        v-model:gender="dynamicGender"
        v-model:avatar="dynamicAvatar"
        :loading="dynamicLoading"
        :success="dynamicSuccess"
        :success-message="dynamicSuccessMessage"
        :error="dynamicError"
        :errors="dynamicErrors"
        @submit="createDynamicBarcode"
        @clear-error="clearDynamicError"
      />

      <!-- Transfer Dynamic Barcode Section -->
      <TransferBarcodeForm
        v-model:html="transferHtml"
        :loading="transferLoading"
        :success="transferSuccess"
        :success-message="transferSuccessMessage"
        :error="transferError"
        :errors="transferErrors"
        @submit="transferDynamicBarcode"
        @clear-error="clearTransferError"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { emitsDefinition, propsDefinition, useAddBarcodeCardSetup } from './AddBarcodeCard.setup';
import CameraPermissionBanner from '@dashboard/components/shared/CameraPermissionBanner.vue';
import DynamicBarcodeForm from '@dashboard/components/barcodes/add/DynamicBarcodeForm.vue';
import TransferBarcodeForm from '@dashboard/components/barcodes/add/TransferBarcodeForm.vue';

defineProps(propsDefinition);
const emit = defineEmits(emitsDefinition);

const {
  addSectionLocal,
  newBarcode,
  errors,
  // Dynamic barcode with profile
  dynamicBarcode,
  dynamicName,
  dynamicInformationId,
  dynamicGender,
  dynamicAvatar,
  dynamicLoading,
  dynamicSuccess,
  dynamicSuccessMessage,
  dynamicError,
  dynamicErrors,
  // Transfer dynamic barcode
  transferHtml,
  transferLoading,
  transferSuccess,
  transferSuccessMessage,
  transferError,
  transferErrors,
  // Scanner
  showScanner,
  scanning,
  scannerStatus,
  videoRef,
  cameras,
  selectedCameraId,
  toggleScanner,
  // Camera permission
  hasCameraPermission,
  isRequestingPermission,
  requestCameraPermission,
  // Methods
  clearError,
  addBarcode,
  clearDynamicError,
  createDynamicBarcode,
  clearTransferError,
  transferDynamicBarcode,
} = useAddBarcodeCardSetup({ emit });
</script>
