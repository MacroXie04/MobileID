import { ref } from 'vue';
import { useApi } from '@shared/composables/useApi';
import { useBarcodeScanner } from '@dashboard/composables/barcode/useBarcodeScanner.js';

export function useAddBarcodeLogic(emit) {
  const { apiCreateBarcode, apiTransferCatCard } = useApi();

  // Barcode state
  const addSectionLocal = ref(null);
  const newBarcode = ref('');
  const errors = ref({});

  // Scanner composable
  const { showScanner, scanning, scannerStatus, videoRef, cameras, selectedCameraId, toggleScanner } =
    useBarcodeScanner({
      onScan: (code) => {
        newBarcode.value = code;
        emit('message', 'Barcode scanned successfully!', 'success');
      },
      onError: (error) => {
        emit('message', error.message || 'Scanner error occurred', 'danger');
      },
    });

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
        } else if (
          error.status === 400 &&
          error.message &&
          error.message.includes('barcode with this barcode already exists')
        ) {
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

  return {
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
    requestTransferCode
  };
}

