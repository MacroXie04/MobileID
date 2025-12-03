<template>
  <section ref="addSectionLocal" class="dashboard-card md-mb-6">
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>add_circle</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small">Add New Barcode</h2>
        <p class="md-typescale-body-small header-subtitle">
          Add UC Merced dynamic barcode or static barcode
        </p>
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
      <div v-if="!hasCameraPermission" class="permission-banner">
        <div class="permission-banner-icon">
          <md-icon>videocam_off</md-icon>
        </div>
        <div class="permission-banner-content">
          <span class="permission-banner-title">Camera Permission Required</span>
          <span class="permission-banner-desc"
            >Enable camera access to scan barcodes with camera</span
          >
        </div>
        <md-filled-tonal-button :disabled="isRequestingPermission" @click="requestCameraPermission">
          <md-icon slot="icon">{{
            isRequestingPermission ? 'hourglass_empty' : 'videocam'
          }}</md-icon>
          {{ isRequestingPermission ? 'Requesting...' : 'Allow' }}
        </md-filled-tonal-button>
      </div>

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
      <div class="settings-section">
        <div class="active-barcode-header">
          <md-icon class="active-icon">school</md-icon>
          <span class="md-typescale-label-medium">UC Merced Dynamic Barcode</span>
        </div>

        <div class="active-barcode-info-wrapper">
          <form class="md-form" @submit.prevent="createDynamicBarcode">
            <div class="transfer-form md-p-4">
              <div class="form-grid">
                <md-outlined-text-field
                  v-model="dynamicBarcode"
                  :error="!!dynamicErrors.barcode"
                  :error-text="dynamicErrors.barcode"
                  class="full-width"
                  label="Barcode Number (14 digits)"
                  maxlength="14"
                  placeholder="Enter 14 digit barcode"
                  @input="clearDynamicError('barcode')"
                >
                  <md-icon slot="leading-icon">qr_code_2</md-icon>
                </md-outlined-text-field>

                <md-outlined-text-field
                  v-model="dynamicName"
                  :error="!!dynamicErrors.name"
                  :error-text="dynamicErrors.name"
                  class="full-width md-mt-4"
                  label="Full Name"
                  placeholder="Enter your full name"
                  @input="clearDynamicError('name')"
                >
                  <md-icon slot="leading-icon">person</md-icon>
                </md-outlined-text-field>

                <md-outlined-text-field
                  v-model="dynamicInformationId"
                  :error="!!dynamicErrors.information_id"
                  :error-text="dynamicErrors.information_id"
                  class="full-width md-mt-4"
                  label="Student ID"
                  placeholder="Enter your student ID"
                  @input="clearDynamicError('information_id')"
                >
                  <md-icon slot="leading-icon">badge</md-icon>
                </md-outlined-text-field>

                <div class="md-mt-4">
                  <label class="md-typescale-body-small select-label">Gender</label>
                  <md-outlined-select v-model="dynamicGender" class="full-width">
                    <md-select-option value="Male">
                      <div slot="headline">Male</div>
                    </md-select-option>
                    <md-select-option value="Female">
                      <div slot="headline">Female</div>
                    </md-select-option>
                    <md-select-option value="Unknow">
                      <div slot="headline">Prefer not to say</div>
                    </md-select-option>
                  </md-outlined-select>
                </div>

                <div class="md-mt-4">
                  <label class="md-typescale-body-small select-label">Avatar (optional)</label>
                  <textarea
                    v-model="dynamicAvatar"
                    :class="['avatar-textarea', { 'has-error': !!dynamicErrors.avatar }]"
                    placeholder="Paste image data URI, e.g. data:image/jpeg;base64,..."
                    rows="3"
                    @input="clearDynamicError('avatar')"
                  ></textarea>
                  <span v-if="dynamicErrors.avatar" class="error-text">{{
                    dynamicErrors.avatar
                  }}</span>
                  <span v-else class="helper-text"
                    >Paste the full img src value (data:image/jpeg;base64,... or
                    data:image/png;base64,...)</span
                  >
                </div>
              </div>

              <div class="form-actions md-flex md-gap-3 md-mt-4">
                <md-filled-button :disabled="dynamicLoading" type="submit">
                  <md-icon slot="icon">add</md-icon>
                  Create Dynamic Barcode
                </md-filled-button>
              </div>
            </div>

            <transition name="fade">
              <div v-if="dynamicSuccess" class="md-banner md-banner-success md-mx-4 md-mb-4">
                <md-icon>check_circle</md-icon>
                <span class="md-typescale-body-medium">
                  {{ dynamicSuccessMessage || 'Dynamic barcode created successfully!' }}
                </span>
              </div>
            </transition>

            <transition name="fade">
              <div v-if="dynamicError" class="md-banner md-banner-error md-mx-4 md-mb-4">
                <md-icon>error</md-icon>
                <span class="md-typescale-body-medium">{{ dynamicError }}</span>
              </div>
            </transition>
          </form>
        </div>
      </div>

      <!-- Transfer Dynamic Barcode Section -->
      <div class="settings-section md-mt-6">
        <div class="active-barcode-header">
          <md-icon class="active-icon">swap_horiz</md-icon>
          <span class="md-typescale-label-medium">Transfer Dynamic Barcode</span>
        </div>

        <div class="active-barcode-info-wrapper">
          <form class="md-form" @submit.prevent="transferDynamicBarcode">
            <div class="transfer-form md-p-4">
              <div class="form-grid">
                <div>
                  <label class="md-typescale-body-small select-label">HTML Content</label>
                  <textarea
                    v-model="transferHtml"
                    :class="['transfer-textarea', { 'has-error': !!transferErrors.html }]"
                    placeholder="Paste the raw HTML from your ID card page..."
                    rows="6"
                    @input="clearTransferError"
                  ></textarea>
                  <span v-if="transferErrors.html" class="error-text">{{
                    transferErrors.html
                  }}</span>
                  <span v-else class="helper-text"
                    >Paste the complete HTML source of your ID card page. The system will
                    automatically extract barcode, name, student ID, and avatar.</span
                  >
                </div>
              </div>

              <div class="form-actions md-flex md-gap-3 md-mt-4">
                <md-filled-button :disabled="transferLoading || !transferHtml.trim()" type="submit">
                  <md-icon slot="icon">{{
                    transferLoading ? 'hourglass_empty' : 'upload'
                  }}</md-icon>
                  {{ transferLoading ? 'Transferring...' : 'Transfer Barcode' }}
                </md-filled-button>
              </div>
            </div>

            <transition name="fade">
              <div v-if="transferSuccess" class="md-banner md-banner-success md-mx-4 md-mb-4">
                <md-icon>check_circle</md-icon>
                <span class="md-typescale-body-medium">
                  {{ transferSuccessMessage || 'Dynamic barcode transferred successfully!' }}
                </span>
              </div>
            </transition>

            <transition name="fade">
              <div v-if="transferError" class="md-banner md-banner-error md-mx-4 md-mb-4">
                <md-icon>error</md-icon>
                <span class="md-typescale-body-medium">{{ transferError }}</span>
              </div>
            </transition>
          </form>
        </div>
      </div>
    </div>
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
