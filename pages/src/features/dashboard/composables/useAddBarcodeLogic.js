import { ref } from 'vue';
import { useApi } from '@shared/composables/useApi';
import { useBarcodeScanner } from '@dashboard/composables/barcode/useBarcodeScanner.js';

export function useAddBarcodeLogic(emit) {
  const { apiCreateBarcode, apiCreateDynamicBarcodeWithProfile, apiTransferDynamicBarcode } =
    useApi();

  // Barcode state
  const addSectionLocal = ref(null);
  const newBarcode = ref('');
  const errors = ref({});

  // Permission state
  const isRequestingPermission = ref(false);
  const permissionDenied = ref(false);

  // Scanner composable
  const {
    showScanner,
    scanning,
    scannerStatus,
    videoRef,
    cameras,
    selectedCameraId,
    toggleScanner,
    hasCameraPermission,
    ensureCameraPermission,
  } = useBarcodeScanner({
    onScan: (code) => {
      newBarcode.value = code;
      emit('message', 'Barcode scanned successfully!', 'success');
    },
    onError: (error) => {
      emit('message', error.message || 'Scanner error occurred', 'danger');
    },
  });

  // Request camera permission
  async function requestCameraPermission() {
    isRequestingPermission.value = true;
    permissionDenied.value = false;
    try {
      const { granted } = await ensureCameraPermission({
        facingMode: 'environment',
        stopStream: true,
      });
      if (!granted) {
        permissionDenied.value = true;
      }
    } catch (error) {
      console.error('Permission request error:', error);
      permissionDenied.value = true;
    } finally {
      isRequestingPermission.value = false;
    }
  }

  // Dynamic barcode with profile state
  const dynamicBarcode = ref('');
  const dynamicName = ref('');
  const dynamicInformationId = ref('');
  const dynamicGender = ref('Unknow');
  const dynamicAvatar = ref('');
  const dynamicLoading = ref(false);
  const dynamicSuccess = ref(false);
  const dynamicSuccessMessage = ref('');
  const dynamicError = ref('');
  const dynamicErrors = ref({});

  // Transfer dynamic barcode state
  const transferHtml = ref('');
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

  function clearDynamicError(field) {
    delete dynamicErrors.value[field];
    dynamicError.value = '';
    dynamicSuccess.value = false;
    dynamicSuccessMessage.value = '';
  }

  async function createDynamicBarcode() {
    try {
      dynamicError.value = '';
      dynamicSuccess.value = false;
      dynamicSuccessMessage.value = '';
      dynamicErrors.value = {};

      // Validate required fields
      let hasError = false;
      if (!dynamicBarcode.value || !dynamicBarcode.value.trim()) {
        dynamicErrors.value.barcode = 'Barcode is required';
        hasError = true;
      } else {
        const barcodeValue = dynamicBarcode.value.trim();
        if (!/^\d+$/.test(barcodeValue)) {
          dynamicErrors.value.barcode = 'Barcode must contain only digits';
          hasError = true;
        } else if (barcodeValue.length !== 14) {
          dynamicErrors.value.barcode = 'Barcode must be exactly 14 digits';
          hasError = true;
        }
      }

      if (!dynamicName.value || !dynamicName.value.trim()) {
        dynamicErrors.value.name = 'Name is required';
        hasError = true;
      }

      if (!dynamicInformationId.value || !dynamicInformationId.value.trim()) {
        dynamicErrors.value.information_id = 'Student ID is required';
        hasError = true;
      }

      if (hasError) return;

      dynamicLoading.value = true;

      // Build request data
      const requestData = {
        barcode: dynamicBarcode.value.trim(),
        name: dynamicName.value.trim(),
        information_id: dynamicInformationId.value.trim(),
        gender: dynamicGender.value,
      };

      // Include avatar if provided
      if (dynamicAvatar.value && dynamicAvatar.value.trim()) {
        requestData.avatar = dynamicAvatar.value.trim();
      }

      const data = await apiCreateDynamicBarcodeWithProfile(requestData);

      if (data && data.status === 'success') {
        dynamicSuccess.value = true;
        dynamicSuccessMessage.value =
          data.message || 'Dynamic barcode with profile created successfully!';
        // Clear form
        dynamicBarcode.value = '';
        dynamicName.value = '';
        dynamicInformationId.value = '';
        dynamicGender.value = 'Unknow';
        dynamicAvatar.value = '';
        emit('message', dynamicSuccessMessage.value, 'success');
        emit('added');
      } else {
        dynamicError.value = data?.message || 'Failed to create dynamic barcode';
      }
    } catch (error) {
      if (error.status === 400 && error.errors) {
        // Handle field-specific errors and build detailed message
        const fieldErrors = [];
        if (error.errors.barcode) {
          const msg = Array.isArray(error.errors.barcode)
            ? error.errors.barcode[0]
            : error.errors.barcode;
          dynamicErrors.value.barcode = msg;
          fieldErrors.push(`Barcode: ${msg}`);
        }
        if (error.errors.name) {
          const msg = Array.isArray(error.errors.name) ? error.errors.name[0] : error.errors.name;
          dynamicErrors.value.name = msg;
          fieldErrors.push(`Name: ${msg}`);
        }
        if (error.errors.information_id) {
          const msg = Array.isArray(error.errors.information_id)
            ? error.errors.information_id[0]
            : error.errors.information_id;
          dynamicErrors.value.information_id = msg;
          fieldErrors.push(`Student ID: ${msg}`);
        }
        if (error.errors.avatar) {
          const msg = Array.isArray(error.errors.avatar)
            ? error.errors.avatar[0]
            : error.errors.avatar;
          dynamicErrors.value.avatar = msg;
          fieldErrors.push(`Avatar: ${msg}`);
        }
        // Show specific field errors if available, otherwise show generic message
        dynamicError.value =
          fieldErrors.length > 0 ? fieldErrors.join('; ') : error.message || 'Invalid request';
      } else if (error.status === 403) {
        dynamicError.value = 'Only School group users can create dynamic barcodes';
      } else {
        dynamicError.value = error.message || 'Network error occurred';
      }
    } finally {
      dynamicLoading.value = false;
    }
  }

  function clearTransferError() {
    transferErrors.value = {};
    transferError.value = '';
    transferSuccess.value = false;
    transferSuccessMessage.value = '';
  }

  async function transferDynamicBarcode() {
    try {
      transferError.value = '';
      transferSuccess.value = false;
      transferSuccessMessage.value = '';
      transferErrors.value = {};

      // Validate HTML content
      if (!transferHtml.value || !transferHtml.value.trim()) {
        transferErrors.value.html = 'HTML content is required';
        return;
      }

      transferLoading.value = true;

      const data = await apiTransferDynamicBarcode(transferHtml.value);

      if (data && data.status === 'success') {
        transferSuccess.value = true;
        transferSuccessMessage.value = data.message || 'Dynamic barcode transferred successfully!';
        // Clear form
        transferHtml.value = '';
        emit('message', transferSuccessMessage.value, 'success');
        emit('added');
      } else {
        transferError.value = data?.message || 'Failed to transfer dynamic barcode';
      }
    } catch (error) {
      if (error.status === 400 && error.errors) {
        // Handle field-specific errors and build detailed message
        const fieldErrors = [];
        if (error.errors.html) {
          const msg = Array.isArray(error.errors.html) ? error.errors.html[0] : error.errors.html;
          transferErrors.value.html = msg;
          fieldErrors.push(msg);
        }
        if (error.errors.barcode) {
          const msg = Array.isArray(error.errors.barcode)
            ? error.errors.barcode[0]
            : error.errors.barcode;
          transferErrors.value.barcode = msg;
          fieldErrors.push(`Barcode: ${msg}`);
        }
        if (error.errors.name) {
          const msg = Array.isArray(error.errors.name) ? error.errors.name[0] : error.errors.name;
          transferErrors.value.name = msg;
          fieldErrors.push(`Name: ${msg}`);
        }
        if (error.errors.information_id) {
          const msg = Array.isArray(error.errors.information_id)
            ? error.errors.information_id[0]
            : error.errors.information_id;
          transferErrors.value.information_id = msg;
          fieldErrors.push(`Student ID: ${msg}`);
        }
        // Show specific field errors if available, otherwise show generic message
        transferError.value =
          fieldErrors.length > 0 ? fieldErrors.join('; ') : 'Could not parse HTML content';
      } else if (error.status === 403) {
        transferError.value = 'Only School group users can transfer dynamic barcodes';
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
    permissionDenied,
    requestCameraPermission,
    // Methods
    clearError,
    addBarcode,
    clearDynamicError,
    createDynamicBarcode,
    clearTransferError,
    transferDynamicBarcode,
  };
}
