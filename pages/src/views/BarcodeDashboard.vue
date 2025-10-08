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
        <div class="chip-wrapper" @click="setTab('Overview')">
          <md-filter-chip :selected="activeTab === 'Overview'">
            Overview
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Barcodes')">
          <md-filter-chip :selected="activeTab === 'Barcodes'">
            Available Barcodes
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Add')">
          <md-filter-chip :selected="activeTab === 'Add'">
            Transfer & Add Barcode
          </md-filter-chip>
        </div>
      </div>

      <!-- Barcode Settings -->
      <SettingsCard
          v-show="activeTab === 'Overview'"
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
          v-show="activeTab === 'Barcodes'"
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
          v-show="activeTab === 'Add'"
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
import {computed, nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
import {useRouter, useRoute} from 'vue-router';
import {useApi} from '@/composables/useApi';
import {useDailyLimit} from '@/composables/useDailyLimit';
import {formatRelativeTime, formatDate, normalize} from '@/utils/dateUtils';
import {
  getBarcodeDisplayTitle,
  getBarcodeDisplayId,
  getBarcodeTypeLabel,
  getProfileLabel,
  getProfileTooltip,
  getAssociationStatusText
} from '@/utils/barcodeUtils';
import SettingsCard from '@/components/dashboard/SettingsCard.vue';
import BarcodesListCard from '@/components/dashboard/BarcodesListCard.vue';
import AddBarcodeCard from '@/components/dashboard/AddBarcodeCard.vue';
import '@/assets/css/BarcodeDashboard.css';

// Router
const router = useRouter();
const route = useRoute();

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
  applyLimitPreset: applyLimitPresetBase
} = useDailyLimit(apiUpdateBarcodeDailyLimit, showMessage);

// Wrapper functions that pass barcodes ref
const updateDailyLimit = (barcode, value) => updateDailyLimitBase(barcode, value, barcodes);
const incrementDailyLimit = (barcode) => incrementDailyLimitBase(barcode, barcodes);
const decrementDailyLimit = (barcode) => decrementDailyLimitBase(barcode, barcodes);
const toggleUnlimitedSwitch = (barcode, event) => toggleUnlimitedSwitchBase(barcode, event, barcodes);
const applyLimitPreset = (barcode, value) => applyLimitPresetBase(barcode, value, barcodes);

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

// Dialog state
const showConfirmDialog = ref(false);
const barcodeToDelete = ref(null);

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


// Filter state
const filterType = ref('All'); // All | Dynamic | Static | Identification
const ownedOnly = ref(false);

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

// Note: Filter reset functionality available if needed in future
// Add barcode functionality moved to AddBarcodeCard component

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

// Daily limit functions are now provided by useDailyLimit composable

function goToAddTab() {
  activeTab.value = 'Add';
}

function setTab(tab) {
  activeTab.value = tab;
}

// Setting change handler with debouncing
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


// Scanner functionality has been moved to AddBarcodeCard component
// Utility functions (date formatting, barcode formatting) imported from utils

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
  // Initialize tab from URL (?tab=Overview|Barcodes|Add)
  const initialTab = (route.query.tab || 'Overview');
  if (['Overview','Barcodes','Add'].includes(initialTab)) {
    activeTab.value = initialTab;
  }
  loadDashboard();
});

// Keep URL in sync with tab
watch(activeTab, (tab) => {
  const q = {...route.query, tab};
  router.replace({ query: q }).catch(() => {});
});

onUnmounted(() => {
  // Clear save timeout
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  // Daily limit timeout cleanup handled by useDailyLimit composable
});
</script>

<!-- Styles moved to external CSS: see @/assets/css/BarcodeDashboard.css -->
