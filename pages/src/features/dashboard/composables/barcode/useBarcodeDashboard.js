// Composable for BarcodeDashboard state and logic
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useApi } from '@shared/composables/useApi';

export default function useBarcodeDashboard() {
  // API
  const {
    apiGetBarcodeDashboard,
    apiUpdateBarcodeSettings,
    apiCreateBarcode,
    apiDeleteBarcode,
    apiUpdateBarcodeShare,
    apiUpdateBarcodeDailyLimit,
  } = useApi();

  // Reactive state
  const loading = ref(true);
  const message = ref('');
  const messageType = ref('success');
  const errors = ref({});
  const isSaving = ref(false);

  // Dashboard data
  const settings = ref({
    associate_user_profile_with_barcode: false,
    barcode: null,
  });
  const barcodes = ref([]);
  const barcodeChoices = ref([]);
  const isUserGroup = ref(false);
  const isSchoolGroup = ref(false);

  const isDynamicSelected = computed(() => {
    if (!settings.value.barcode) return false;
    const current = barcodeChoices.value.find(
      (c) => Number(c.id) === Number(settings.value.barcode)
    );
    return current?.barcode_type === 'DynamicBarcode';
  });

  const currentBarcodeHasProfile = computed(() => {
    if (!settings.value.barcode) return false;
    const current = barcodeChoices.value.find(
      (c) => Number(c.id) === Number(settings.value.barcode)
    );
    return current?.has_profile_addon || false;
  });

  // Selected barcode (full object)
  const selectedBarcode = computed(() => {
    if (!settings.value.barcode) return null;
    const id = Number(settings.value.barcode);
    return (barcodes.value || []).find((b) => Number(b.id) === id) || null;
  });

  // Form state
  const newBarcode = ref('');

  // Scanner state
  const showScanner = ref(false);
  const scanning = ref(false);
  const scannerStatus = ref('Position the barcode within the camera view');
  const videoRef = ref(null);
  let codeReader = null;
  const cameras = ref([]);
  const selectedCameraId = ref(null);
  const hasCameraPermission = ref(false);

  // Dialog
  const showConfirmDialog = ref(false);
  const barcodeToDelete = ref(null);

  // Template refs
  const addSection = ref(null);

  function clearError(field) {
    delete errors.value[field];
  }

  function showMessage(msg, type = 'success') {
    message.value = msg;
    messageType.value = type;
    setTimeout(() => {
      message.value = '';
    }, 5000);
  }

  async function loadDashboard() {
    try {
      loading.value = true;
      const data = await apiGetBarcodeDashboard();

      // Reset then set
      settings.value = {
        associate_user_profile_with_barcode: false,
        barcode: null,
      };
      barcodeChoices.value = [];

      // Choices first
      barcodeChoices.value = data.settings.barcode_choices || [];

      await nextTick();

      settings.value = {
        associate_user_profile_with_barcode: Boolean(
          data.settings.associate_user_profile_with_barcode
        ),
        barcode: data.settings.barcode ? Number(data.settings.barcode) : null,
      };

      barcodes.value = data.barcodes || [];
      isUserGroup.value = Boolean(data.is_user_group);
      isSchoolGroup.value = Boolean(data.is_school_group);
    } catch (error) {
      showMessage('Failed to load dashboard: ' + (error?.message || 'Unknown error'), 'danger');
    } finally {
      loading.value = false;
    }
  }

  // Debounced settings save
  let saveTimeout = null;

  async function autoSaveSettings() {
    const startTime = Date.now();
    try {
      isSaving.value = true;
      errors.value = {};

      const settingsToSend = {
        ...settings.value,
        barcode: settings.value.barcode ? Number(settings.value.barcode) : null,
      };

      const response = await apiUpdateBarcodeSettings(settingsToSend);

      if (response?.status === 'success') {
        if (response.settings?.barcode_choices) {
          barcodeChoices.value = response.settings.barcode_choices;
        }
        if (response.settings && response.settings.barcode !== undefined) {
          settings.value.barcode = response.settings.barcode
            ? Number(response.settings.barcode)
            : null;
        }
        if (
          response.settings &&
          response.settings.associate_user_profile_with_barcode !== undefined
        ) {
          settings.value.associate_user_profile_with_barcode = Boolean(
            response.settings.associate_user_profile_with_barcode
          );
        }
      }

      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 1000 - elapsed);
      if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));
    } catch (error) {
      if (error?.status === 400 && error?.errors) {
        errors.value = error.errors;
      } else {
        showMessage('Failed to save settings: ' + (error?.message || 'Unknown error'), 'danger');
      }
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 1000 - elapsed);
      if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));
    } finally {
      isSaving.value = false;
    }
  }

  // Filters
  const filterType = ref('All');
  const ownedOnly = ref(false);

  const filteredBarcodes = computed(() => {
    let result = [...(barcodes.value || [])];
    if (ownedOnly.value) {
      result = result.filter((b) => b.is_owned_by_current_user);
    }
    if (filterType.value !== 'All') {
      if (filterType.value === 'Dynamic') {
        result = result.filter((b) => b.barcode_type === 'DynamicBarcode');
      } else if (filterType.value === 'Static') {
        result = result.filter((b) => b.barcode_type === 'Others');
      } else if (filterType.value === 'Identification') {
        result = result.filter((b) => b.barcode_type === 'Identification');
      }
    }
    return result;
  });

  function onFilterChange() {
    // No-op; kept for explicit bindings
  }

  const hasActiveFilters = computed(() => filterType.value !== 'All' || ownedOnly.value);

  function resetFilters() {
    filterType.value = 'All';
    ownedOnly.value = false;
  }

  // CRUD actions
  async function addBarcode() {
    try {
      errors.value = {};
      if (!newBarcode.value.trim()) {
        errors.value.newBarcode = 'Barcode is required';
        return;
      }
      const response = await apiCreateBarcode(newBarcode.value);
      if (response?.status === 'success') {
        showMessage(response.message, 'success');
        newBarcode.value = '';
        await loadDashboard();
      }
    } catch (error) {
      if (error?.status === 400 && error?.errors) {
        if (error.errors.barcode && error.errors.barcode.length > 0) {
          errors.value.newBarcode = error.errors.barcode[0];
        } else if (
          error.message &&
          error.message.includes('barcode with this barcode already exists')
        ) {
          errors.value.newBarcode = 'Barcode already exists';
        } else {
          errors.value.newBarcode = 'Invalid barcode';
        }
      } else {
        showMessage('Failed to add barcode', 'danger');
      }
    }
  }

  async function deleteBarcode(barcode) {
    if (!barcode || !barcode.is_owned_by_current_user) {
      showMessage('You can only delete your own barcode', 'danger');
      return;
    }
    barcodeToDelete.value = barcode.id;
    showConfirmDialog.value = true;
  }

  async function confirmDelete() {
    if (!barcodeToDelete.value) return;
    try {
      const response = await apiDeleteBarcode(barcodeToDelete.value);
      if (response?.status === 'success') {
        showMessage(response.message, 'success');
        await loadDashboard();
      }
    } catch (error) {
      showMessage('Failed to delete barcode: ' + (error?.message || 'Unknown error'), 'danger');
    } finally {
      showConfirmDialog.value = false;
      barcodeToDelete.value = null;
    }
  }

  async function toggleShare(barcode) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    try {
      const nextValue = !barcode.share_with_others;
      const res = await apiUpdateBarcodeShare(barcode.id, nextValue);
      if (res?.status === 'success' && res?.barcode) {
        const idx = barcodes.value.findIndex((b) => Number(b.id) === Number(barcode.id));
        if (idx !== -1) {
          barcodes.value[idx] = {
            ...barcodes.value[idx],
            share_with_others: res.barcode.share_with_others,
          };
        }
        showMessage(nextValue ? 'Sharing enabled' : 'Sharing disabled', 'success');
      }
    } catch (e) {
      showMessage('Failed to update sharing: ' + (e?.message || 'Unknown error'), 'danger');
    }
  }

  // Daily limit (debounced)
  let dailyLimitTimeout = null;

  async function updateDailyLimit(barcode, value) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    if (dailyLimitTimeout) clearTimeout(dailyLimitTimeout);
    dailyLimitTimeout = setTimeout(async () => {
      try {
        const limit = parseInt(value, 10) || 0;
        if (limit < 0) {
          showMessage('Daily limit must be 0 or greater', 'danger');
          return;
        }
        const res = await apiUpdateBarcodeDailyLimit(barcode.id, limit);
        if (res?.status === 'success' && res?.barcode) {
          const idx = barcodes.value.findIndex((b) => Number(b.id) === Number(barcode.id));
          if (idx !== -1) {
            barcodes.value[idx] = {
              ...barcodes.value[idx],
              daily_usage_limit: res.barcode.daily_usage_limit,
              usage_stats: res.barcode.usage_stats,
            };
          }
          showMessage(`Daily limit set to ${limit === 0 ? 'unlimited' : limit}`, 'success');
        }
      } catch (e) {
        showMessage('Failed to update daily limit: ' + (e?.message || 'Unknown error'), 'danger');
      }
    }, 1000);
  }

  function scrollToAdd() {
    if (addSection.value) {
      addSection.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function formatRelativeTime(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }

  // Display helpers
  function getBarcodeDisplayTitle(barcodeType) {
    switch (barcodeType) {
      case 'DynamicBarcode':
        return 'Dynamic Barcode';
      case 'Others':
        return 'Barcode';
      case 'Identification':
        return 'Identification Barcode';
      default:
        return 'Barcode';
    }
  }

  function getBarcodeDisplayId(barcode) {
    switch (barcode.barcode_type) {
      case 'DynamicBarcode':
        return `Dynamic •••• ${barcode.barcode.slice(-4)}`;
      case 'Others':
        return `Barcode ending with ${barcode.barcode.slice(-4)}`;
      case 'Identification':
        return 'Identification Barcode';
      default:
        return `•••• ${barcode.barcode.slice(-4)}`;
    }
  }

  function getBarcodeTypeLabel(type) {
    if (type === 'DynamicBarcode') return 'Dynamic';
    if (type === 'Identification') return 'Identification';
    return 'Static';
  }

  function getProfileLabel(barcode) {
    if (!barcode.profile_info) return 'Profile';
    const { name, information_id, has_avatar } = barcode.profile_info;
    if (name && name.length <= 15) return name;
    if (information_id) {
      if (information_id.length > 8 && /^\d+$/.test(information_id)) {
        return `ID: ${information_id.slice(-4)}`;
      }
      return `ID: ${information_id}`;
    }
    return has_avatar ? 'Profile+' : 'Profile';
  }

  function getProfileTooltip(barcode) {
    if (!barcode.profile_info) return 'Profile attached';
    const { name, information_id, has_avatar } = barcode.profile_info;
    const parts = [];
    if (name) parts.push(`Name: ${name}`);
    if (information_id) parts.push(`ID: ${information_id}`);
    if (has_avatar) parts.push('Has avatar image');
    return parts.length ? parts.join('\n') : 'Profile attached';
  }

  function onSettingChange() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      autoSaveSettings();
    }, 800);
  }

  async function setActiveBarcode(barcode) {
    if (!barcode) return;
    if (Number(settings.value.barcode) === Number(barcode.id)) return;
    settings.value.barcode = Number(barcode.id);
    await autoSaveSettings();
  }

  // Scanner
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
        showMessage('Camera permission is required to use the scanner.', 'danger');
        return;
      }
      await startScanner();
    }
  }

  async function startScanner() {
    try {
      scanning.value = true;
      scannerStatus.value = 'Initializing scanner...';

      const { BrowserMultiFormatReader } = await import('@zxing/library');
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

      codeReader.decodeFromVideoDevice(selectedCameraId.value, videoRef.value, (result, error) => {
        if (result) {
          newBarcode.value = result.getText();
          showMessage('Barcode scanned successfully!', 'success');
          stopScanner();
        }
        if (error && error.name !== 'NotFoundException') {
          // Non-fatal errors while scanning
        }
      });
    } catch (error) {
      scannerStatus.value = `Failed to start scanner: ${error?.message || 'Unknown error'}`;
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
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      stream.getTracks().forEach((t) => t.stop());
      hasCameraPermission.value = true;
      return true;
    } catch (err) {
      hasCameraPermission.value = false;
      if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
        scannerStatus.value = 'Camera permission was denied. Please enable it in browser settings.';
      } else if (err && err.name === 'NotFoundError') {
        scannerStatus.value = 'No camera device found.';
      } else {
        scannerStatus.value = `Unable to access camera: ${err?.message || 'Unknown error'}`;
      }
      return false;
    }
  }

  // Derived
  const currentBarcodeInfo = computed(() => {
    if (!settings.value.barcode) return null;
    const current = barcodeChoices.value.find(
      (c) => Number(c.id) === Number(settings.value.barcode)
    );
    if (!current) return null;
    if (current.barcode_type === 'Identification') {
      return `${current.barcode_type}`;
    }
    return `${current.barcode_type} ending with ...${current.barcode.slice(-4)}`;
  });

  // Watchers
  watch(selectedCameraId, async (newId, oldId) => {
    if (showScanner.value && newId && oldId && newId !== oldId) {
      if (codeReader) codeReader.reset();
      await nextTick();
      await startScanner();
    }
  });

  watch(showScanner, (newValue) => {
    if (!newValue) {
      stopScanner();
    }
  });

  // Lifecycle
  onMounted(() => {
    loadDashboard();
  });

  onUnmounted(() => {
    stopScanner();
    if (saveTimeout) clearTimeout(saveTimeout);
    if (dailyLimitTimeout) clearTimeout(dailyLimitTimeout);
  });

  return {
    // state
    loading,
    message,
    messageType,
    errors,
    isSaving,
    settings,
    barcodes,
    barcodeChoices,
    isUserGroup,
    isSchoolGroup,
    isDynamicSelected,
    currentBarcodeHasProfile,
    selectedBarcode,
    newBarcode,
    // scanner
    showScanner,
    scanning,
    scannerStatus,
    videoRef,
    cameras,
    selectedCameraId,
    // dialog
    showConfirmDialog,
    // refs
    addSection,
    // computeds
    filteredBarcodes,
    hasActiveFilters,
    currentBarcodeInfo,
    // filters
    filterType,
    ownedOnly,
    // methods
    clearError,
    loadDashboard,
    onFilterChange,
    resetFilters,
    addBarcode,
    deleteBarcode,
    confirmDelete,
    toggleShare,
    updateDailyLimit,
    scrollToAdd,
    formatRelativeTime,
    onSettingChange,
    setActiveBarcode,
    toggleScanner,
    formatDate,
    getBarcodeDisplayTitle,
    getBarcodeDisplayId,
    getBarcodeTypeLabel,
    getProfileLabel,
    getProfileTooltip,
  };
}
