<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h1 class="md-typescale-display-small md-m-0">Barcode Management</h1>
          <p class="md-typescale-body-large md-m-0 md-mt-1">Configure and manage your digital ID barcodes</p>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Flash Messages -->
    <transition name="slide-down">
      <div v-if="message" :class="['message-toast', 'md-banner', messageType === 'success' ? 'md-banner-success' : 'md-banner-error']">
        <md-icon>{{ messageType === 'success' ? 'check_circle' : 'error' }}</md-icon>
        <span class="md-typescale-body-medium">{{ message }}</span>
        <md-icon-button @click="message = ''">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="md-content">
      <!-- Settings Card -->
      <section class="md-card md-mb-6">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>tune</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">Barcode Settings</h2>
          <transition name="fade">
            <div v-if="isSaving" class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto">
              <md-circular-progress indeterminate></md-circular-progress>
              <span class="md-typescale-body-small">Saving...</span>
            </div>
          </transition>
        </div>

        <div class="settings-content">
          <!-- Active Barcode Display -->
          <div v-if="currentBarcodeInfo" class="active-barcode-display md-flex md-items-center md-gap-3 md-p-4 md-rounded-lg md-mb-6">
            <md-icon>badge</md-icon>
            <div class="active-info">
              <span class="md-typescale-label-large">Active Barcode</span>
              <span class="md-typescale-body-medium">{{ currentBarcodeInfo }}</span>
            </div>
          </div>

          <div class="settings-grid md-flex md-flex-column md-gap-4">
            <!-- Profile Association -->
            <div class="setting-item md-flex md-items-center md-justify-between md-p-4 md-rounded-lg">
              <div class="setting-header md-flex md-gap-3">
                <md-icon>person_pin</md-icon>
                <div>
                  <h3 class="md-typescale-title-medium md-m-0">Profile Association</h3>
                  <p class="md-typescale-body-small md-m-0 md-mt-1">Link your user profile to the active barcode</p>
                </div>
              </div>
              
              <md-switch
                v-model="settings.associate_user_profile_with_barcode"
                :disabled="isUserGroup"
                @change="onSettingChange"
              ></md-switch>
            </div>

            <!-- Server Verification -->
            <div class="setting-item md-flex md-items-center md-justify-between md-p-4 md-rounded-lg">
              <div class="setting-header md-flex md-gap-3">
                <md-icon>security</md-icon>
                <div>
                  <h3 class="md-typescale-title-medium md-m-0">Server Verification</h3>
                  <p class="md-typescale-body-small md-m-0 md-mt-1">Enable server-side barcode validation</p>
                </div>
              </div>
              
              <md-switch
                v-model="settings.server_verification"
                @change="onSettingChange"
              ></md-switch>
            </div>
          </div>

          <div v-if="Object.keys(errors).length > 0" class="md-banner md-banner-error md-mt-4">
            <md-icon>error</md-icon>
            <div class="error-messages">
              <p v-for="(error, field) in errors" :key="field" class="md-typescale-body-medium md-m-0">
                {{ error }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Barcodes List -->
      <section class="md-card md-mb-6">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>inventory_2</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">My Barcodes</h2>
        </div>

        <!-- Filter Bar -->
        <div class="filter-bar md-flex md-gap-3 md-items-center md-mb-6 md-flex-wrap">
          <md-outlined-text-field
            v-model="searchQuery"
            class="search-field md-flex-1"
            placeholder="Search by owner or barcode digits"
            @input="onFilterChange"
          >
            <md-icon slot="leading-icon">search</md-icon>
          </md-outlined-text-field>

          <div class="filter-controls md-flex md-items-center md-gap-2">
            <md-filter-chip
              :selected="filterType === 'All'"
              @click="filterType = 'All'; onFilterChange()"
            >
              All
            </md-filter-chip>
            <md-filter-chip
              :selected="filterType === 'Dynamic'"
              @click="filterType = 'Dynamic'; onFilterChange()"
            >
              Dynamic
            </md-filter-chip>
            <md-filter-chip
              :selected="filterType === 'Static'"
              @click="filterType = 'Static'; onFilterChange()"
            >
              Static
            </md-filter-chip>
            
            <md-divider vertical></md-divider>
            
            <md-filter-chip
              :selected="ownedOnly"
              @click="ownedOnly = !ownedOnly; onFilterChange()"
            >
              <md-icon slot="icon">person</md-icon>
              Owned only
            </md-filter-chip>
          </div>

          <md-outlined-select v-model="sortBy" class="sort-select" @change="onFilterChange">
            <md-select-option value="Newest">
              <div slot="headline">Newest first</div>
            </md-select-option>
            <md-select-option value="Oldest">
              <div slot="headline">Oldest first</div>
            </md-select-option>
            <md-select-option value="MostUsed">
              <div slot="headline">Most used</div>
            </md-select-option>
          </md-outlined-select>
        </div>

        <!-- Barcodes Grid -->
        <transition-group
          v-if="filteredBarcodes.length > 0"
          name="list"
          tag="div"
          class="barcodes-grid md-grid-container md-gap-4"
        >
          <article
            v-for="barcode in filteredBarcodes"
            :key="barcode.id"
            class="barcode-item md-card md-p-5 md-flex md-items-center md-gap-4"
            :class="{
              'is-active': Number(settings.barcode) === Number(barcode.id),
              'is-shared': !barcode.is_owned_by_current_user
            }"
          >
            <!-- Barcode Type Icon -->
            <div class="barcode-type-icon md-flex md-items-center md-justify-center md-rounded-lg">
              <md-icon>
                {{ barcode.barcode_type === 'DynamicBarcode' ? 'qr_code_2' : 'barcode' }}
              </md-icon>
            </div>

            <!-- Barcode Content -->
            <div class="barcode-content">
              <div class="barcode-title-row">
                <h3 class="md-typescale-title-medium md-m-0">
                  {{ barcode.barcode_type === 'DynamicBarcode' ? 'Dynamic' : 'Static' }} Barcode
                </h3>
                <div class="barcode-badges md-flex md-gap-2 md-flex-wrap">
                  <span v-if="Number(settings.barcode) === Number(barcode.id)" class="md-badge badge-active">
                    <md-icon>check_circle</md-icon>
                    Active
                  </span>
                  <span v-if="!barcode.is_owned_by_current_user" class="md-badge badge-shared">
                    <md-icon>group</md-icon>
                    Shared
                  </span>
                  <span v-if="barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon" class="md-badge badge-addon">
                    <md-icon>badge</md-icon>
                    Profile
                  </span>
                </div>
              </div>

              <p class="barcode-id md-typescale-body-medium md-mt-2 md-mb-0">
                •••• {{ barcode.barcode.slice(-4) }}
                <span v-if="!barcode.is_owned_by_current_user" class="owner-label">
                  by {{ barcode.owner }}
                </span>
              </p>

              <div v-if="barcode.usage_count > 0" class="barcode-stats md-flex md-gap-4 md-flex-wrap md-mt-3">
                <span class="stat md-flex md-items-center md-gap-1">
                  <md-icon>trending_up</md-icon>
                  {{ barcode.usage_count }} scan{{ barcode.usage_count !== 1 ? 's' : '' }}
                </span>
                <span v-if="barcode.last_used" class="stat md-flex md-items-center md-gap-1">
                  <md-icon>schedule</md-icon>
                  {{ formatRelativeTime(barcode.last_used) }}
                </span>
              </div>
            </div>

            <!-- Barcode Actions -->
            <div class="barcode-actions md-flex md-items-center md-gap-2">
              <md-filled-tonal-button
                v-if="Number(settings.barcode) !== Number(barcode.id)"
                @click="setActiveBarcode(barcode)"
              >
                <md-icon slot="icon">check_circle</md-icon>
                Set Active
              </md-filled-tonal-button>
              
              <md-icon-button
                v-if="barcode.is_owned_by_current_user"
                @click="deleteBarcode(barcode)"
              >
                <md-icon>delete</md-icon>
              </md-icon-button>
            </div>
          </article>
        </transition-group>

        <!-- Empty State -->
        <div v-else class="md-empty-state">
          <md-icon class="md-empty-state-icon">qr_code_scanner</md-icon>
          <h3 class="md-typescale-headline-small md-mb-2">No barcodes found</h3>
          <p class="md-typescale-body-medium md-m-0">
            {{ searchQuery || filterType !== 'All' || ownedOnly 
              ? 'Try adjusting your filters' 
              : 'Add your first barcode to get started' }}
          </p>
        </div>
      </section>

      <!-- Add Barcode Section -->
      <section ref="addSection" class="md-card">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>add_circle</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">Add New Barcode</h2>
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
              <md-outlined-button
                type="button"
                @click="toggleScanner"
              >
                <md-icon slot="icon">
                  {{ showScanner ? 'videocam_off' : 'qr_code_scanner' }}
                </md-icon>
                {{ showScanner ? 'Close Scanner' : 'Scan with Camera' }}
              </md-outlined-button>

              <md-filled-button type="submit" :disabled="!newBarcode.trim()">
                <md-icon slot="icon">add</md-icon>
                Add Barcode
              </md-filled-button>
            </div>
          </div>

          <!-- Scanner Section -->
          <transition name="expand">
            <div v-if="showScanner" class="scanner-container md-card md-card-filled md-rounded-lg md-p-5 md-mt-6">
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
                <video
                  ref="videoRef"
                  autoplay
                  muted
                  playsinline
                  webkit-playsinline
                ></video>
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
import {nextTick, onMounted, onUnmounted, ref, watch, computed} from 'vue';
import {useRouter} from 'vue-router';
import {useApi} from '@/composables/useApi';

// Router
const router = useRouter();

// API composable
const {
  apiGetBarcodeDashboard,
  apiUpdateBarcodeSettings,
  apiCreateBarcode,
  apiDeleteBarcode
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
  server_verification: false,
  barcode: null
});
const barcodes = ref([]);
const barcodeChoices = ref([]);
const isUserGroup = ref(false);
const isSchoolGroup = ref(false);

// Form data
const newBarcode = ref('');

// Scanner state
const showScanner = ref(false);
const scanning = ref(false);
const scannerStatus = ref('Position the barcode within the camera view');
const videoRef = ref(null);
let codeReader = null;
const cameras = ref([]);
const selectedCameraId = ref(null);

// Dialog state
const showConfirmDialog = ref(false);
const barcodeToDelete = ref(null);

// Template refs
const addSection = ref(null);

// Clear specific error
const clearError = (field) => {
  delete errors.value[field];
};

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

  } catch (error) {
    showMessage('Failed to load dashboard: ' + error.message, 'danger');
  } finally {
    loading.value = false;
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
const filterType = ref('All'); // All | Dynamic | Static
const sortBy = ref('Newest'); // Newest | Oldest | MostUsed
const ownedOnly = ref(false);

function normalize(str) {
  try { return String(str || '').toLowerCase(); } catch { return ''; }
}

const filteredBarcodes = computed(() => {
  let result = [...(barcodes.value || [])];

  if (ownedOnly.value) {
    result = result.filter(b => b.is_owned_by_current_user);
  }

  if (filterType.value !== 'All') {
    const wantDynamic = filterType.value === 'Dynamic';
    result = result.filter(b => (b.barcode_type === 'DynamicBarcode') === wantDynamic || (b.barcode_type !== 'DynamicBarcode') === !wantDynamic);
  }

  const q = normalize(searchQuery.value);
  if (q) {
    result = result.filter(b => {
      const owner = normalize(b.owner);
      const value = String(b.barcode || '');
      return owner.includes(q) || value.includes(q);
    });
  }

  if (sortBy.value === 'Newest') {
    result.sort((a, b) => new Date(b.time_created) - new Date(a.time_created));
  } else if (sortBy.value === 'Oldest') {
    result.sort((a, b) => new Date(a.time_created) - new Date(b.time_created));
  } else if (sortBy.value === 'MostUsed') {
    result.sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0));
  }

  return result;
});

function onFilterChange() {
  // Computed handles updates. This is here for explicit @change bindings.
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

// Scroll to add section
function scrollToAdd() {
  if (addSection.value) {
    addSection.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
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
    await startScanner();
  }
}

async function startScanner() {
  try {
    scanning.value = true;
    scannerStatus.value = 'Initializing scanner...';

    const {BrowserMultiFormatReader} = await import('@zxing/library');
    codeReader = new BrowserMultiFormatReader();

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

// Get current barcode info
const currentBarcodeInfo = computed(() => {
  if (!settings.value.barcode) return null;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  if (!current) return null;
  return `${current.barcode_type} ending with ...${current.barcode.slice(-8)}`;
});


// Lifecycle
onMounted(() => {
  loadDashboard();
});

onUnmounted(() => {
  stopScanner();
  // Clear save timeout
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
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

watch(showScanner, (newValue) => {
  if (!newValue) {
    stopScanner();
  }
});
</script>

<style scoped>
/* Page-specific styles for BarcodeDashboard.vue - minimal overrides only */

/* Message Toast positioning */
.message-toast {
  position: fixed;
  top: 88px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 600px;
}

/* Header card icon colors */
.card-header md-icon {
  color: var(--md-sys-color-primary);
}

/* Action Cards */
.action-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover {
  transform: translateY(-2px);
}

.action-icon {
  font-size: 48px;
}

.action-icon.primary {
  color: var(--md-sys-color-primary);
}

.action-icon.secondary {
  color: var(--md-sys-color-secondary);
}

.action-icon.tertiary {
  color: var(--md-sys-color-tertiary);
}

/* Settings Section */
.active-barcode-display {
  background: var(--md-sys-color-primary-container);
}

.active-barcode-display md-icon {
  color: var(--md-sys-color-on-primary-container);
}

.active-info {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-1);
}

.setting-item {
  background: var(--md-sys-color-surface-container);
}

.setting-header {
  flex: 1;
}

.setting-header md-icon {
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 2px;
}

/* Save indicator */
.save-indicator md-circular-progress {
  --md-circular-progress-size: 20px;
}

/* Filter Bar */
.search-field {
  min-width: 200px;
}

.sort-select {
  min-width: 150px;
}

/* Barcode Items */
.barcode-item {
  transition: all 0.2s ease;
  display: grid;
  grid-template-columns: auto 1fr auto;
}

.barcode-item.is-active {
  background: var(--md-sys-color-primary-container);
}

.barcode-item.is-shared {
  background: var(--md-sys-color-surface-container-low);
}

.barcode-item:hover {
  background: var(--md-sys-color-surface-container-high);
}

.barcode-item.is-active:hover {
  background: var(--md-sys-color-primary-container);
}

.barcode-type-icon {
  width: 56px;
  height: 56px;
  background: var(--md-sys-color-surface-container-highest);
}

.barcode-type-icon md-icon {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

.barcode-content {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-2);
}

.barcode-title-row {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-3);
  flex-wrap: wrap;
}

/* Badge overrides */
.badge-active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.badge-shared {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.badge-addon {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.md-badge md-icon {
  font-size: 14px;
}

.barcode-id {
  font-family: 'Roboto Mono', monospace;
  color: var(--md-sys-color-on-surface-variant);
}

.owner-label {
  color: var(--md-sys-color-primary);
  font-weight: 500;
}

.stat {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-body-small-size);
}

.stat md-icon {
  font-size: 16px;
}

/* Scanner Container */
.scanner-header md-icon {
  color: var(--md-sys-color-primary);
}

.scanner-viewport {
  position: relative;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  aspect-ratio: 4/3;
  background: #000;
  overflow: hidden;
}

.scanner-viewport video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scanner-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.scanner-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 60%;
  border: 3px solid var(--md-sys-color-primary);
  border-radius: var(--md-sys-shape-corner-medium);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
}

/* Camera select */
.camera-select {
  min-width: 200px;
}

/* Transitions */
.list-enter-active,
.list-leave-active,
.list-move {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translate(-50%, -100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translate(-50%, -100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 600px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 904px) {
  .md-grid-cols-3 {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-field {
    width: 100%;
  }
  
  .filter-controls {
    overflow-x: auto;
    padding-bottom: var(--md-sys-spacing-1);
  }
  
  .barcode-item {
    grid-template-columns: 1fr;
  }
  
  .barcode-type-icon {
    display: none;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions > * {
    width: 100%;
  }
}

@media (max-width: 599px) {
  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--md-sys-spacing-3);
  }
}
</style> 