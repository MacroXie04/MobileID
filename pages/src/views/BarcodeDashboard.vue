<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h3 class="md-typescale-title-medium md-m-0">Barcode Dashboard</h3>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Flash Messages -->
    <transition name="slide-down">
      <div v-if="message"
           :class="['message-toast', 'md-banner', messageType === 'success' ? 'md-banner-success' : 'md-banner-error']">
        <md-icon>{{ messageType === 'success' ? 'check_circle' : 'error' }}</md-icon>
        <span class="md-typescale-body-medium">{{ message }}</span>
        <md-icon-button @click="message = ''">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="md-content">
      <!-- Tabs Navigation -->
      <div class="tabs-bar md-flex md-gap-2 md-items-center md-mb-6">
        <md-filter-chip :selected="activeTab === 'Overview'" @click="activeTab = 'Overview'">
          Overview
        </md-filter-chip>
        <md-filter-chip :selected="activeTab === 'Barcodes'" @click="activeTab = 'Barcodes'">
          Available Barcodes
        </md-filter-chip>
        <md-filter-chip :selected="activeTab === 'Add'" @click="activeTab = 'Add'">
          Transfer & Add Barcode
        </md-filter-chip>
      </div>

      <!-- Barcode Settings -->
      <SettingsCard
          v-if="activeTab === 'Overview'"
          :is-saving="isSaving"
          :current-barcode-info="currentBarcodeInfo"
          :selected-barcode="selectedBarcode"
          :barcode-choices="barcodeChoices"
          :settings="settings"
          :is-user-group="isUserGroup"
          :is-dynamic-selected="isDynamicSelected"
          :current-barcode-has-profile="currentBarcodeHasProfile"
          :errors="errors"
          :associate-user-profile-with-barcode="Boolean(settings.associate_user_profile_with_barcode)"
          :server-verification="Boolean(settings.server_verification)"
          :format-relative-time="formatRelativeTime"
          :format-date="formatDate"
          @update-associate="(val) => { settings.associate_user_profile_with_barcode = val; onSettingChange(); }"
          @update-server="(val) => { settings.server_verification = val; onSettingChange(); }"
      />

      <!-- Barcodes List -->
      <BarcodesListCard
          :active-tab="activeTab"
          :settings="settings"
          :filtered-barcodes="filteredBarcodes"
          :has-active-filters="hasActiveFilters"
          :filter-type="filterType"
          :owned-only="ownedOnly"
          :updating-limit="updatingLimit"
          @update-filter="(val) => { filterType = val; onFilterChange(); }"
          @toggle-owned="() => { ownedOnly = !ownedOnly; onFilterChange(); }"
          @set-active="setActiveBarcode"
          @toggle-share="toggleShare"
          @delete="deleteBarcode"
          @update-limit="updateDailyLimit"
          @increment-limit="incrementDailyLimit"
          @decrement-limit="decrementDailyLimit"
          @toggle-unlimited-switch="toggleUnlimitedSwitch"
          @apply-limit-preset="applyLimitPreset"
      />

      <!-- Add Barcode Section -->
      <AddBarcodeCard
          :active-tab="activeTab"
          @added="loadDashboard"
          @message="showMessage"
      />
      <!-- Floating Action Button to Add -->
      <md-fab style="position: fixed; right: 24px; bottom: 24px; z-index: 10;" @click="goToAddTab">
        <md-icon slot="icon">add</md-icon>
        <div slot="label">Add Barcode</div>
      </md-fab>
    </main>

    <!-- Delete Confirmation Dialog -->
    <md-dialog :open="showConfirmDialog" @close="showConfirmDialog = false">
      <div slot="headline">Delete Barcode?</div>
      <form slot="content" method="dialog">
        <p class="md-typescale-body-large">
          This will permanently delete the barcode. This action cannot be undone.
        </p>
      </form>
      <div slot="actions">
        <md-text-button @click="showConfirmDialog = false">Cancel</md-text-button>
        <md-filled-button @click="confirmDelete">Delete</md-filled-button>
      </div>
    </md-dialog>
  </div>
</template>

<script setup>
import {computed, nextTick, onMounted, onUnmounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import {useApi} from '@/composables/useApi';
import SettingsCard from '@/components/dashboard/SettingsCard.vue';
import BarcodesListCard from '@/components/dashboard/BarcodesListCard.vue';
import AddBarcodeCard from '@/components/dashboard/AddBarcodeCard.vue';
import '@/assets/css/BarcodeDashboard.css';

// Router
const router = useRouter();

// API composable
const {
  apiGetBarcodeDashboard,
  apiUpdateBarcodeSettings,
  apiCreateBarcode,
  apiDeleteBarcode,
  apiGetActiveProfile,
  apiUpdateBarcodeShare,
  apiUpdateBarcodeDailyLimit
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
  server_verification: false,
  barcode: null
});
const barcodes = ref([]);
const barcodeChoices = ref([]);
const isUserGroup = ref(false);
const isSchoolGroup = ref(false);
const isDynamicSelected = computed(() => {
  if (!settings.value.barcode) return false;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  return current?.barcode_type === 'DynamicBarcode';
});

const currentBarcodeHasProfile = computed(() => {
  if (!settings.value.barcode) return false;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  return current?.has_profile_addon || false;
});

// Selected barcode full object (from barcodes list)
const selectedBarcode = computed(() => {
  if (!settings.value.barcode) return null;
  const id = Number(settings.value.barcode);
  return (barcodes.value || []).find(b => Number(b.id) === id) || null;
});

// Form data
const newBarcode = ref('');

// Scanner state moved to AddBarcodeCard component

// Per-barcode daily limit updating state
const updatingLimit = ref({});

// Dialog state
const showConfirmDialog = ref(false);
const barcodeToDelete = ref(null);

// Template refs moved to AddBarcodeCard component

// Clear specific error
const clearError = (field) => {
  delete errors.value[field];
};

// Transfer section moved into TransferBarcode component

// Load dashboard data
async function loadDashboard() {
  try {
    loading.value = true;
    const data = await apiGetBarcodeDashboard();

    // Clear previous state
    settings.value = {
      associate_user_profile_with_barcode: false,
      server_verification: false,
      barcode: null
    };
    barcodeChoices.value = [];

    // Set choices first
    barcodeChoices.value = data.settings.barcode_choices || [];

    // Then set settings with proper type conversion
    await nextTick(); // Wait for choices to be rendered

    settings.value = {
      associate_user_profile_with_barcode: Boolean(data.settings.associate_user_profile_with_barcode),
      server_verification: Boolean(data.settings.server_verification),
      barcode: data.settings.barcode ? Number(data.settings.barcode) : null
    };

    barcodes.value = data.barcodes || [];
    isUserGroup.value = Boolean(data.is_user_group);
    isSchoolGroup.value = Boolean(data.is_school_group);

    // Check for active profile (for School users with barcode profile association)
    await checkActiveProfile();

  } catch (error) {
    showMessage('Failed to load dashboard: ' + error.message, 'danger');
  } finally {
    loading.value = false;
  }
}

// Check and apply active profile
async function checkActiveProfile() {
  try {
    console.log('Dashboard: Checking active profile...');
    const response = await apiGetActiveProfile();
    console.log('Dashboard: Active profile response:', response);

    if (response && response.profile_info) {
      console.log('Dashboard: Active profile found, updating page title and info');
      // Show a brief notification about active profile association
      showMessage(`Profile Association Active: ${response.profile_info.name}`, 'success');
    } else {
      console.log('Dashboard: No active profile association');
    }
  } catch (error) {
    console.error('Dashboard: Failed to check active profile:', error);
  }
}

// Auto-save settings with debounce
let saveTimeout = null;

async function autoSaveSettings() {
  // Record start time for minimum display duration
  const startTime = Date.now();

  try {
    isSaving.value = true;
    errors.value = {};

    // ensure barcode ID is a number
    const settingsToSend = {
      ...settings.value,
      barcode: settings.value.barcode ? Number(settings.value.barcode) : null
    };

    const response = await apiUpdateBarcodeSettings(settingsToSend);

    if (response.status === 'success') {
      // update choices from response
      if (response.settings && response.settings.barcode_choices) {
        barcodeChoices.value = response.settings.barcode_choices;
      }
      // Ensure the updated barcode value is properly typed
      if (response.settings && response.settings.barcode !== undefined) {
        settings.value.barcode = response.settings.barcode ? Number(response.settings.barcode) : null;
      }
      // Update association status from backend
      if (response.settings && response.settings.associate_user_profile_with_barcode !== undefined) {
        settings.value.associate_user_profile_with_barcode = Boolean(response.settings.associate_user_profile_with_barcode);
      }
    }

    // Ensure minimum display time of 1 second
    const elapsed = Date.now() - startTime;
    const remainingTime = Math.max(0, 1000 - elapsed);

    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime));
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
      await new Promise(resolve => setTimeout(resolve, remainingTime));
    }
  } finally {
    isSaving.value = false;
  }
}

// Deprecated - kept for backward compatibility
async function updateSettings() {
  await autoSaveSettings();
}

// Filter/sort state and helpers
const searchQuery = ref('');
const filterType = ref('All'); // All | Dynamic | Static | Identification
const sortBy = ref('Newest'); // Newest | Oldest | MostUsed
const ownedOnly = ref(false);

function normalize(str) {
  try {
    return String(str || '').toLowerCase();
  } catch {
    return '';
  }
}

const filteredBarcodes = computed(() => {
  let result = [...(barcodes.value || [])];

  if (ownedOnly.value) {
    result = result.filter(b => b.is_owned_by_current_user);
  }

  if (filterType.value !== 'All') {
    if (filterType.value === 'Dynamic') {
      result = result.filter(b => b.barcode_type === 'DynamicBarcode');
    } else if (filterType.value === 'Static') {
      result = result.filter(b => b.barcode_type === 'Others');
    } else if (filterType.value === 'Identification') {
      result = result.filter(b => b.barcode_type === 'Identification');
    }
  }

  // removed search and sort controls; keep default ordering from API

  return result;
});

function onFilterChange() {
  // Computed handles updates. This is here for explicit @change bindings.
}

const hasActiveFilters = computed(() => {
  return filterType.value !== 'All' || ownedOnly.value;
});

function resetFilters() {
  filterType.value = 'All';
  ownedOnly.value = false;
}

// Add new barcode
async function addBarcode() {
  try {
    errors.value = {};

    if (!newBarcode.value.trim()) {
      errors.value.newBarcode = 'Barcode is required';
      return;
    }

    const response = await apiCreateBarcode(newBarcode.value);

    if (response.status === 'success') {
      showMessage(response.message, 'success');
      newBarcode.value = '';
      // Reload dashboard to get updated data
      await loadDashboard();
    }
  } catch (error) {
    if (error.status === 400 && error.errors) {
      // Handle validation errors from API
      if (error.errors.barcode && error.errors.barcode.length > 0) {
        errors.value.newBarcode = error.errors.barcode[0];
      } else if (error.status === 400 && error.message && error.message.includes('barcode with this barcode already exists')) {
        errors.value.newBarcode = 'Barcode already exists';
      } else {
        errors.value.newBarcode = 'Invalid barcode';
      }
    } else {
      showMessage('Failed to add barcode', 'danger');
    }
  }
}

// Delete barcode
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

// Toggle share_with_others for an owned barcode
async function toggleShare(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  try {
    const next = !barcode.share_with_others;
    const res = await apiUpdateBarcodeShare(barcode.id, next);
    if (res?.status === 'success' && res?.barcode) {
      // Update local list entry optimistically with server echo
      const idx = barcodes.value.findIndex(b => Number(b.id) === Number(barcode.id));
      if (idx !== -1) {
        barcodes.value[idx] = {...barcodes.value[idx], share_with_others: res.barcode.share_with_others};
      }
      showMessage(next ? 'Sharing enabled' : 'Sharing disabled', 'success');
    }
  } catch (e) {
    showMessage('Failed to update sharing: ' + (e?.message || 'Unknown error'), 'danger');
  }
}

// Update daily usage limit with debounce
let dailyLimitTimeout = null;

async function updateDailyLimit(barcode, value) {
  if (!barcode || !barcode.is_owned_by_current_user) return;

  // Clear previous timeout
  if (dailyLimitTimeout) {
    clearTimeout(dailyLimitTimeout);
  }

  // Debounce for 1 second
  dailyLimitTimeout = setTimeout(async () => {
    try {
      const limit = parseInt(value) || 0;
      if (limit < 0) {
        showMessage('Daily limit must be 0 or greater', 'danger');
        return;
      }

      updatingLimit.value = {...updatingLimit.value, [barcode.id]: true};
      const res = await apiUpdateBarcodeDailyLimit(barcode.id, limit);
      if (res?.status === 'success' && res?.barcode) {
        // Update local barcode data
        const idx = barcodes.value.findIndex(b => Number(b.id) === Number(barcode.id));
        if (idx !== -1) {
          barcodes.value[idx] = {
            ...barcodes.value[idx],
            daily_usage_limit: res.barcode.daily_usage_limit,
            usage_stats: res.barcode.usage_stats
          };
        }
        showMessage(`Daily limit set to ${limit === 0 ? 'unlimited' : limit}`, 'success');
      }
    } catch (e) {
      showMessage('Failed to update daily limit: ' + (e?.message || 'Unknown error'), 'danger');
    } finally {
      updatingLimit.value = {...updatingLimit.value, [barcode.id]: false};
    }
  }, 1000);
}

function incrementDailyLimit(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const current = Number(barcode.daily_usage_limit || 0);
  const next = current === 0 ? 1 : current + 1;
  // Optimistic UI update
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

function decrementDailyLimit(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const current = Number(barcode.daily_usage_limit || 0);
  const next = Math.max(0, current - 1);
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

function toggleUnlimited(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const next = (Number(barcode.daily_usage_limit || 0) === 0) ? 1 : 0;
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

// Switch handler to set unlimited directly from the header switch
function toggleUnlimitedSwitch(barcode, event) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const selected = Boolean(event?.target?.selected);
  const next = selected ? 0 : (Number(barcode.daily_usage_limit || 0) === 0 ? 1 : Number(barcode.daily_usage_limit));
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

// Apply preset values quickly
function applyLimitPreset(barcode, value) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const limit = Math.max(0, Number(value) || 0);
  // If currently unlimited and preset > 0, turn off unlimited
  barcode.daily_usage_limit = limit === 0 ? 0 : limit;
  updateDailyLimit(barcode, limit);
}

function goToAddTab() {
  activeTab.value = 'Add';
}

// Format relative time
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

// setting change handler
function onSettingChange() {
  // debounce logic, 800ms delay to avoid frequent api calls
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }

  saveTimeout = setTimeout(() => {
    autoSaveSettings();
  }, 800);
}

// Set active barcode directly from the list
async function setActiveBarcode(barcode) {
  if (!barcode) return;
  // No-op if already active
  if (Number(settings.value.barcode) === Number(barcode.id)) return;
  settings.value.barcode = Number(barcode.id);
  await autoSaveSettings();
}


// Scanner functions
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
            showMessage('Barcode scanned successfully!', 'success');
            stopScanner();
          }

          if (error && error.name !== 'NotFoundException') {
            // This error is expected when no barcode is in view.
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
    const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}});
    // Immediately stop tracks; we only needed to trigger permission
    stream.getTracks().forEach(t => t.stop());
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

// Utility functions
function showMessage(msg, type = 'success') {
  message.value = msg;
  messageType.value = type;

  // Auto-hide after 5 seconds
  setTimeout(() => {
    message.value = '';
  }, 5000);
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Get association status text
function getAssociationStatusText() {
  if (settings.value.associate_user_profile_with_barcode) {
    return 'Active - Profile associated with barcode';
  }
  return 'Inactive - No profile association';
}

// Get barcode display title
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

// Get barcode display ID
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

  const {name, information_id, has_avatar} = barcode.profile_info;

  // Show name if available and not too long
  if (name && name.length <= 15) {
    return name;
  }

  // Show information ID if available and name is too long or not available
  if (information_id) {
    // Show last 4 digits if it's a long ID number
    if (information_id.length > 8 && /^\d+$/.test(information_id)) {
      return `ID: ${information_id.slice(-4)}`;
    }
    // Show full ID if it's short or contains letters
    return `ID: ${information_id}`;
  }

  // Fallback to generic label with avatar indicator
  return has_avatar ? 'Profile+' : 'Profile';
}

function getProfileTooltip(barcode) {
  if (!barcode.profile_info) return 'Profile attached';

  const {name, information_id, has_avatar} = barcode.profile_info;
  const parts = [];

  if (name) parts.push(`Name: ${name}`);
  if (information_id) parts.push(`ID: ${information_id}`);
  if (has_avatar) parts.push('Has avatar image');

  return parts.length ? parts.join('\n') : 'Profile attached';
}

// Get current barcode info
const currentBarcodeInfo = computed(() => {
  if (!settings.value.barcode) return null;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  if (!current) return null;

  // Check if it's an Identification barcode
  if (current.barcode_type === 'Identification') {
    return `${current.barcode_type}`;
  }

  // For other barcode types, show last 4 digits
  return `${current.barcode_type} ending with ...${current.barcode.slice(-4)}`;
});


// Lifecycle
onMounted(() => {
  loadDashboard();
});

onUnmounted(() => {
  // Clear save timeout
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  // Clear daily limit timeout
  if (dailyLimitTimeout) {
    clearTimeout(dailyLimitTimeout);
  }
});


// Scanner watchers moved to AddBarcodeCard
</script>

<!-- Styles moved to external CSS: see @/assets/css/BarcodeDashboard.css -->