import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useApi } from '@shared/composables/useApi';
import { useDailyLimit } from '@dashboard/composables/barcode/useDailyLimit';

export function useDashboardLogic() {
  const router = useRouter();
  const route = useRoute();

  // API composable
  const {
    apiGetBarcodeDashboard,
    apiUpdateBarcodeSettings,
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

  // Tabs
  const activeTab = ref('Overview');

  // Dashboard data
  const settings = ref({
    associate_user_profile_with_barcode: false,
    scanner_detection_enabled: false,
    prefer_front_camera: true,
    barcode: null,
  });
  const pullSettings = ref({
    pull_setting: 'Disable',
    gender_setting: 'Unknow',
  });
  const barcodes = ref([]);
  const barcodeChoices = ref([]);
  const isUserGroup = ref(false);
  const isSchoolGroup = ref(false);

  // Filter state
  const filterType = ref('All'); // All | Dynamic | Static | Identification
  const ownedOnly = ref(false);

  // Dialog state
  const showConfirmDialog = ref(false);
  const barcodeToDelete = ref(null);

  // Auto-save settings with debounce
  let saveTimeout = null;

  // Utility function for showing messages
  function showMessage(msg, type = 'success') {
    message.value = msg;
    messageType.value = type;

    // Auto-hide after 5 seconds
    setTimeout(() => {
      message.value = '';
    }, 5000);
  }

  // Daily limit management composable
  const {
    updatingLimit,
    updateDailyLimit: updateDailyLimitBase,
    incrementDailyLimit: incrementDailyLimitBase,
    decrementDailyLimit: decrementDailyLimitBase,
    toggleUnlimitedSwitch: toggleUnlimitedSwitchBase,
    applyLimitPreset: applyLimitPresetBase,
  } = useDailyLimit(apiUpdateBarcodeDailyLimit, showMessage);

  // Wrapper functions that pass barcodes ref
  const updateDailyLimit = (barcode, value) => updateDailyLimitBase(barcode, value, barcodes);
  const incrementDailyLimit = (barcode) => incrementDailyLimitBase(barcode, barcodes);
  const decrementDailyLimit = (barcode) => decrementDailyLimitBase(barcode, barcodes);
  const toggleUnlimitedSwitch = (barcode, event) =>
    toggleUnlimitedSwitchBase(barcode, event, barcodes);
  const applyLimitPreset = (barcode, value) => applyLimitPresetBase(barcode, value, barcodes);

  // Computed Properties
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

  const selectedBarcode = computed(() => {
    if (!settings.value.barcode) return null;
    const id = Number(settings.value.barcode);
    return (barcodes.value || []).find((b) => Number(b.id) === id) || null;
  });

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

  const hasActiveFilters = computed(() => {
    return filterType.value !== 'All' || ownedOnly.value;
  });

  const currentBarcodeInfo = computed(() => {
    if (!settings.value.barcode) return null;
    const current = barcodeChoices.value.find(
      (c) => Number(c.id) === Number(settings.value.barcode)
    );
    if (!current) return null;

    // Check if it's an Identification barcode
    if (current.barcode_type === 'Identification') {
      return `${current.barcode_type}`;
    }

    // For other barcode types, show last 4 digits
    return `${current.barcode_type} ending with ...${current.barcode.slice(-4)}`;
  });

  // Methods
  async function loadDashboard() {
    try {
      loading.value = true;
      const data = await apiGetBarcodeDashboard();

      // Clear previous state
      settings.value = {
        associate_user_profile_with_barcode: false,
        scanner_detection_enabled: false,
        prefer_front_camera: true,
        barcode: null,
      };
      pullSettings.value = {
        pull_setting: 'Disable',
        gender_setting: 'Unknow',
      };
      barcodeChoices.value = [];

      // Set choices first
      barcodeChoices.value = data.settings.barcode_choices || [];

      // Then set settings with proper type conversion
      await nextTick(); // Wait for choices to be rendered

      settings.value = {
        associate_user_profile_with_barcode: Boolean(
          data.settings.associate_user_profile_with_barcode
        ),
        scanner_detection_enabled: Boolean(data.settings.scanner_detection_enabled),
        prefer_front_camera:
          data.settings.prefer_front_camera !== undefined
            ? Boolean(data.settings.prefer_front_camera)
            : true,
        barcode: data.settings.barcode ? Number(data.settings.barcode) : null,
      };

      // Set pull settings if provided
      if (data.pull_settings) {
        pullSettings.value = {
          pull_setting: data.pull_settings.pull_setting || 'Disable',
          gender_setting: data.pull_settings.gender_setting || 'Unknow',
        };
      }

      barcodes.value = data.barcodes || [];
      isUserGroup.value = Boolean(data.is_user_group);
      isSchoolGroup.value = Boolean(data.is_school_group);
    } catch (error) {
      showMessage('Failed to load dashboard: ' + error.message, 'danger');
    } finally {
      loading.value = false;
    }
  }

  async function autoSaveSettings() {
    // Record start time for minimum display duration
    const startTime = Date.now();

    try {
      isSaving.value = true;
      errors.value = {};

      // ensure barcode ID is a number
      const settingsToSend = {
        ...settings.value,
        barcode: settings.value.barcode ? Number(settings.value.barcode) : null,
        pull_settings: pullSettings.value,
      };

      const response = await apiUpdateBarcodeSettings(settingsToSend);

      if (response.status === 'success') {
        // update choices from response
        if (response.settings && response.settings.barcode_choices) {
          barcodeChoices.value = response.settings.barcode_choices;
        }
        // Ensure the updated barcode value is properly typed
        if (response.settings && response.settings.barcode !== undefined) {
          settings.value.barcode = response.settings.barcode
            ? Number(response.settings.barcode)
            : null;
        }
        // Update association status from backend
        if (
          response.settings &&
          response.settings.associate_user_profile_with_barcode !== undefined
        ) {
          settings.value.associate_user_profile_with_barcode = Boolean(
            response.settings.associate_user_profile_with_barcode
          );
        }
        // Update scanner detection settings from backend
        if (response.settings && response.settings.scanner_detection_enabled !== undefined) {
          settings.value.scanner_detection_enabled = Boolean(
            response.settings.scanner_detection_enabled
          );
        }
        if (response.settings && response.settings.prefer_front_camera !== undefined) {
          settings.value.prefer_front_camera = Boolean(response.settings.prefer_front_camera);
        }
        // Update pull settings from backend
        if (response.pull_settings) {
          pullSettings.value = {
            pull_setting: response.pull_settings.pull_setting || 'Disable',
            gender_setting: response.pull_settings.gender_setting || 'Unknow',
          };
        }
      }

      // Ensure minimum display time of 1 second
      const elapsed = Date.now() - startTime;
      const remainingTime = Math.max(0, 1000 - elapsed);

      if (remainingTime > 0) {
        await new Promise((resolve) => setTimeout(resolve, remainingTime));
      }
    } catch (error) {
      if (error.status === 400 && error.errors) {
        errors.value = error.errors;
      } else {
        showMessage('Failed to save settings: ' + error.message, 'danger');
      }

      // Also ensure minimum display time for errors
      const elapsed = Date.now() - startTime;
      const remainingTime = Math.max(0, 1000 - elapsed);

      if (remainingTime > 0) {
        await new Promise((resolve) => setTimeout(resolve, remainingTime));
      }
    } finally {
      isSaving.value = false;
    }
  }

  function onSettingChange() {
    // debounce logic, 800ms delay to avoid frequent api calls
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }

    saveTimeout = setTimeout(() => {
      autoSaveSettings();
    }, 800);
  }

  async function setActiveBarcode(barcode) {
    if (!barcode) return;
    // Check if pull setting is enabled
    if (pullSettings.value.pull_setting === 'Enable') {
      showMessage(
        'Barcode selection is disabled when pull setting is enabled. Please disable pull setting first.',
        'danger'
      );
      return;
    }
    // No-op if already active
    if (Number(settings.value.barcode) === Number(barcode.id)) return;
    settings.value.barcode = Number(barcode.id);
    await autoSaveSettings();
  }

  async function deleteBarcode(barcode) {
    // Guard: only allow deletion for barcodes owned by the current user
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

      if (response.status === 'success') {
        showMessage(response.message, 'success');
        // Reload dashboard to get updated data
        await loadDashboard();
      }
    } catch (error) {
      showMessage('Failed to delete barcode: ' + error.message, 'danger');
    } finally {
      showConfirmDialog.value = false;
      barcodeToDelete.value = null;
    }
  }

  async function toggleShare(barcode) {
    if (!barcode || !barcode.is_owned_by_current_user) return;
    try {
      const next = !barcode.share_with_others;
      const res = await apiUpdateBarcodeShare(barcode.id, next);
      if (res?.status === 'success' && res?.barcode) {
        // Update local list entry optimistically with server echo
        const idx = barcodes.value.findIndex((b) => Number(b.id) === Number(barcode.id));
        if (idx !== -1) {
          barcodes.value[idx] = {
            ...barcodes.value[idx],
            share_with_others: res.barcode.share_with_others,
          };
        }
        showMessage(next ? 'Sharing enabled' : 'Sharing disabled', 'success');
      }
    } catch (e) {
      showMessage('Failed to update sharing: ' + (e?.message || 'Unknown error'), 'danger');
    }
  }

  function onFilterChange(val) {
    if (val) filterType.value = val;
  }

  function toggleOwned() {
    ownedOnly.value = !ownedOnly.value;
  }

  function goToAddTab() {
    activeTab.value = 'Add';
  }

  function setTab(tab) {
    activeTab.value = tab;
  }

  // Lifecycle
  onMounted(() => {
    // Initialize tab from URL (?tab=Overview|Profile|Camera|Barcodes|Add|Devices)
    const initialTab = route.query.tab || 'Overview';
    const allowedTabs = ['Overview', 'Profile', 'Camera', 'Barcodes', 'Add', 'Devices', 'Passkeys'];
    if (allowedTabs.includes(initialTab)) {
      activeTab.value = initialTab;
    }
    loadDashboard();
  });

  onUnmounted(() => {
    // Clear save timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }
  });

  // Watchers
  watch(activeTab, (tab) => {
    const q = { ...route.query, tab };
    router.replace({ query: q }).catch(() => {});
  });

  return {
    loading,
    message,
    messageType,
    errors,
    isSaving,
    activeTab,
    settings,
    pullSettings,
    barcodes,
    barcodeChoices,
    isUserGroup,
    isSchoolGroup,
    filterType,
    ownedOnly,
    showConfirmDialog,
    barcodeToDelete,

    // Computed
    isDynamicSelected,
    currentBarcodeHasProfile,
    selectedBarcode,
    filteredBarcodes,
    hasActiveFilters,
    currentBarcodeInfo,
    updatingLimit,

    // Methods
    loadDashboard,
    onSettingChange,
    setActiveBarcode,
    deleteBarcode,
    confirmDelete,
    toggleShare,
    onFilterChange,
    toggleOwned,
    goToAddTab,
    setTab,
    showMessage,

    // Daily Limit methods
    updateDailyLimit,
    incrementDailyLimit,
    decrementDailyLimit,
    toggleUnlimitedSwitch,
    applyLimitPreset,
  };
}
