import { ref } from 'vue';
import { useBarcodeApi, useBarcodeScanner } from '@barcode';
import type { CreateDynamicBarcodePayload } from '@barcode';
import type { AuthenticatedRequestError } from '@auth';
import { logger } from '@shared/utils/logger';
import type { AddBarcodeEmit } from '@dashboard/types/dashboard';

export function useAddBarcodeLogic(emit: AddBarcodeEmit = () => {}) {
  const { apiCreateBarcode, apiCreateDynamicBarcodeWithProfile, apiTransferDynamicBarcode } =
    useBarcodeApi();

  // Barcode state
  const addSectionLocal = ref(null);
  const newBarcode = ref('');
  const errors = ref<Record<string, string>>({});

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
      logger.error('Permission request error:', error);
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
  const dynamicErrors = ref<Record<string, string>>({});

  // Transfer dynamic barcode state
  const transferHtml = ref('');
  const transferLoading = ref(false);
  const transferSuccess = ref(false);
  const transferSuccessMessage = ref('');
  const transferError = ref('');
  const transferErrors = ref<Record<string, string>>({});

  function clearError(field: string) {
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
      const e = error as AuthenticatedRequestError;
      const errs = e.errors as Record<string, string | string[]> | undefined;
      if (e.status === 400 && errs) {
        if (errs.barcode && errs.barcode.length > 0) {
          errors.value.newBarcode = errs.barcode[0];
        } else if (
          e.status === 400 &&
          e.message &&
          e.message.includes('barcode with this barcode already exists')
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

  function clearDynamicError(field: string) {
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
      const requestData: CreateDynamicBarcodePayload = {
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
      const e = error as AuthenticatedRequestError;
      const errs = e.errors as Record<string, string | string[]> | undefined;
      if (e.status === 400 && errs) {
        // Handle field-specific errors and build detailed message
        const fieldErrors: string[] = [];
        if (errs.barcode) {
          const msg = Array.isArray(errs.barcode) ? errs.barcode[0] : errs.barcode;
          dynamicErrors.value.barcode = msg;
          fieldErrors.push(`Barcode: ${msg}`);
        }
        if (errs.name) {
          const msg = Array.isArray(errs.name) ? errs.name[0] : errs.name;
          dynamicErrors.value.name = msg;
          fieldErrors.push(`Name: ${msg}`);
        }
        if (errs.information_id) {
          const msg = Array.isArray(errs.information_id)
            ? errs.information_id[0]
            : errs.information_id;
          dynamicErrors.value.information_id = msg;
          fieldErrors.push(`Student ID: ${msg}`);
        }
        if (errs.avatar) {
          const msg = Array.isArray(errs.avatar) ? errs.avatar[0] : errs.avatar;
          dynamicErrors.value.avatar = msg;
          fieldErrors.push(`Avatar: ${msg}`);
        }
        // Show specific field errors if available, otherwise show generic message
        dynamicError.value =
          fieldErrors.length > 0 ? fieldErrors.join('; ') : e.message || 'Invalid request';
      } else if (e.status === 403) {
        dynamicError.value = 'Permission denied. Please ensure you are logged in.';
      } else {
        dynamicError.value = e.message || 'Network error occurred';
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
      const e = error as AuthenticatedRequestError;
      const errs = e.errors as Record<string, string | string[]> | undefined;
      if (e.status === 400 && errs) {
        // Handle field-specific errors and build detailed message
        const fieldErrors: string[] = [];
        if (errs.html) {
          const msg = Array.isArray(errs.html) ? errs.html[0] : errs.html;
          transferErrors.value.html = msg;
          fieldErrors.push(msg);
        }
        if (errs.barcode) {
          const msg = Array.isArray(errs.barcode) ? errs.barcode[0] : errs.barcode;
          transferErrors.value.barcode = msg;
          fieldErrors.push(`Barcode: ${msg}`);
        }
        if (errs.name) {
          const msg = Array.isArray(errs.name) ? errs.name[0] : errs.name;
          transferErrors.value.name = msg;
          fieldErrors.push(`Name: ${msg}`);
        }
        if (errs.information_id) {
          const msg = Array.isArray(errs.information_id)
            ? errs.information_id[0]
            : errs.information_id;
          transferErrors.value.information_id = msg;
          fieldErrors.push(`Student ID: ${msg}`);
        }
        // Show specific field errors if available, otherwise show generic message
        transferError.value =
          fieldErrors.length > 0 ? fieldErrors.join('; ') : 'Could not parse HTML content';
      } else if (e.status === 403) {
        transferError.value = 'Permission denied. Please ensure you are logged in.';
      } else {
        transferError.value = e.message || 'Network error occurred';
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
