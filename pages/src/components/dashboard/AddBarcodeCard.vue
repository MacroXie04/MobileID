<template>
  <section ref="addSectionLocal" class="md-card">
    <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
      <md-icon>add_circle</md-icon>
      <h2 class="md-typescale-headline-small md-m-0">Add New Barcode</h2>
    </div>

    <!-- Transfer Barcode (moved from TransferBarcode.vue) -->
    <div class="md-mb-6">
      <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
        <md-icon>cookie</md-icon>
        <h3 class="md-typescale-title-medium md-m-0">Transfer Barcode</h3>
        <transition name="fade">
          <div v-if="transferLoading" class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto">
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
          <md-filled-button @click="requestTransferCode" :disabled="transferLoading || !transferCookie.trim()">
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

          <md-filled-button type="submit" :disabled="!newBarcode.trim()">
            <md-icon slot="icon">add</md-icon>
            Add Barcode
          </md-filled-button>
        </div>
      </div>

      <transition name="expand">
        <div v-if="showScanner" class="scanner-container md-card md-card-filled md-rounded-lg md-p-5 md-mt-6">
          <div class="scanner-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>camera</md-icon>
            <span class="md-typescale-title-medium">Barcode Scanner</span>
            <md-outlined-select v-if="cameras.length > 1" v-model="selectedCameraId" class="camera-select md-ml-auto">
              <md-select-option v-for="device in cameras" :key="device.deviceId" :value="device.deviceId">
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
import {nextTick, ref, watch, onUnmounted} from 'vue';
import {useApi} from '@/composables/useApi';

const emit = defineEmits(['added', 'message']);

const props = defineProps({
  activeTab: { type: String, default: 'Add' }
});

const { apiCreateBarcode, apiTransferCatCard } = useApi();

const addSectionLocal = ref(null);
const newBarcode = ref('');
const errors = ref({});

const showScanner = ref(false);
const scanning = ref(false);
const scannerStatus = ref('Position the barcode within the camera view');
const videoRef = ref(null);
let codeReader = null;
const cameras = ref([]);
const selectedCameraId = ref(null);
const hasCameraPermission = ref(false);

// Transfer state
const transferCookie = ref('');
const transferLoading = ref(false);
const transferSuccess = ref(false);
const transferSuccessMessage = ref('');
const transferError = ref('');
const transferErrors = ref({});

function clearError(field) {
  delete errors.value[field];
}

async function addBarcode() {
  try {
    errors.value = {};
    if (!newBarcode.value.trim()) {
      errors.value.newBarcode = 'Barcode is required';
      return;
    }
    const response = await apiCreateBarcode(newBarcode.value);
    if (response.status === 'success') {
      emit('message', response.message, 'success');
      newBarcode.value = '';
      emit('added');
    }
  } catch (error) {
    if (error.status === 400 && error.errors) {
      if (error.errors.barcode && error.errors.barcode.length > 0) {
        errors.value.newBarcode = error.errors.barcode[0];
      } else if (error.status === 400 && error.message && error.message.includes('barcode with this barcode already exists')) {
        errors.value.newBarcode = 'Barcode already exists';
      } else {
        errors.value.newBarcode = 'Invalid barcode';
      }
    } else {
      emit('message', 'Failed to add barcode', 'danger');
    }
  }
}

function clearTransferError(field) {
  delete transferErrors.value[field];
  transferError.value = '';
  transferSuccess.value = false;
  transferSuccessMessage.value = '';
}

async function requestTransferCode() {
  try {
    transferError.value = '';
    transferSuccess.value = false;
    transferSuccessMessage.value = '';
    transferErrors.value = {};

    if (!transferCookie.value || !transferCookie.value.trim()) {
      transferErrors.value.cookie = 'Cookie is required';
      return;
    }

    transferLoading.value = true;

    const data = await apiTransferCatCard(transferCookie.value);

    if (data && data.success) {
      transferSuccess.value = true;
      transferSuccessMessage.value = data.message || 'Barcode data stored successfully!';
      transferCookie.value = '';
      emit('message', transferSuccessMessage.value, 'success');
      emit('added');
    } else {
      transferError.value = data?.error || 'Transfer failed.';
    }
  } catch (error) {
    if (error.status === 400 && error.errors) {
      transferError.value = error.message || 'Invalid request';
    } else {
      transferError.value = error.message || 'Network error occurred';
    }
  } finally {
    transferLoading.value = false;
  }
}

async function toggleScanner() {
  if (showScanner.value) {
    stopScanner();
    showScanner.value = false;
  } else {
    showScanner.value = true;
    await nextTick();
    const granted = await ensureCameraPermission();
    if (!granted) {
      scanning.value = false;
      scannerStatus.value = 'Camera permission is required to use the scanner.';
      emit('message', 'Camera permission is required to use the scanner.', 'danger');
      return;
    }
    await startScanner();
  }
}

async function startScanner() {
  try {
    scanning.value = true;
    scannerStatus.value = 'Initializing scanner...';
    const {BrowserMultiFormatReader} = await import('@zxing/library');
    codeReader = new BrowserMultiFormatReader();

    if (!hasCameraPermission.value) {
      const granted = await ensureCameraPermission();
      if (!granted) {
        scannerStatus.value = 'Camera permission denied.';
        scanning.value = false;
        return;
      }
    }

    if (cameras.value.length === 0) {
      const videoInputDevices = await codeReader.listVideoInputDevices();
      cameras.value = videoInputDevices;
      if (videoInputDevices.length > 0) {
        if (!selectedCameraId.value) {
          selectedCameraId.value = videoInputDevices[0].deviceId;
        }
      } else {
        scannerStatus.value = 'No cameras found.';
        scanning.value = false;
        return;
      }
    }

    if (!selectedCameraId.value) {
      scannerStatus.value = 'No camera selected.';
      scanning.value = false;
      return;
    }

    scannerStatus.value = 'Position the barcode within the camera view';

    codeReader.decodeFromVideoDevice(
      selectedCameraId.value,
      videoRef.value,
      (result, error) => {
        if (result) {
          newBarcode.value = result.getText();
          emit('message', 'Barcode scanned successfully!', 'success');
          stopScanner();
        }
      }
    );
  } catch (error) {
    scannerStatus.value = `Failed to start scanner: ${error.message}`;
    scanning.value = false;
  }
}

function stopScanner() {
  if (codeReader) {
    codeReader.reset();
    codeReader = null;
  }
  showScanner.value = false;
  scanning.value = false;
  scannerStatus.value = 'Position the barcode within the camera view';
  cameras.value = [];
}

async function ensureCameraPermission() {
  try {
    if (!navigator?.mediaDevices?.getUserMedia) {
      scannerStatus.value = 'Camera is not supported in this browser.';
      return false;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    stream.getTracks().forEach(t => t.stop());
    hasCameraPermission.value = true;
    return true;
  } catch (err) {
    hasCameraPermission.value = false;
    return false;
  }
}

onUnmounted(() => {
  stopScanner();
});

watch(selectedCameraId, async (newId, oldId) => {
  if (showScanner.value && newId && oldId && newId !== oldId) {
    if (codeReader) {
      codeReader.reset();
    }
    await nextTick();
    await startScanner();
  }
});
</script>


