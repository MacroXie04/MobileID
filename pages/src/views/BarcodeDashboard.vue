<template>
  <div class="page-container">
    <div class="page-card dashboard-card">
      <div class="page-header">
        <p class="md-typescale-body-large subtitle">Change & Manage Barcode Settings</p>
      </div>

      <!-- Dashboard Content -->
      <div class="content-section">
        <!-- Flash Messages -->
        <div v-if="message" :class="messageType" class="message-banner">
          <md-icon>{{ messageType === 'success' ? 'check_circle' : 'error_outline' }}</md-icon>
          <span class="md-typescale-body-medium">{{ message }}</span>
          <md-icon-button class="close-button" @click="message = ''">
            <md-icon>close</md-icon>
          </md-icon-button>
        </div>

        <!-- Settings Section -->
        <div class="settings-section">
          <div class="section-header">
            <md-icon>settings</md-icon>
            <h2 class="md-typescale-headline-small">Barcode Settings</h2>
          </div>

          <div class="form-section">
            <div class="settings-grid">
              <!-- Pull Setting -->
              <div class="setting-field">
                <label class="md-typescale-body-large">Barcode Pull</label>
                <md-outlined-select
                    v-model="settings.barcode_pull"
                    :disabled="isUserGroup"
                    @change="onSettingChange"
                >
                  <md-select-option :value="true">
                    <div slot="headline">Yes</div>
                  </md-select-option>
                  <md-select-option :value="false">
                    <div slot="headline">No</div>
                  </md-select-option>
                </md-outlined-select>
                <p v-if="errors.barcode_pull" class="error-text">{{ errors.barcode_pull }}</p>
              </div>

              <!-- Server Verification -->
              <div class="setting-field">
                <label class="md-typescale-body-large">Server Verification</label>
                <md-outlined-select
                    v-model="settings.server_verification"
                    @change="onSettingChange"
                >
                  <md-select-option :value="true">
                    <div slot="headline">Yes</div>
                  </md-select-option>
                  <md-select-option :value="false">
                    <div slot="headline">No</div>
                  </md-select-option>
                </md-outlined-select>
                <p v-if="errors.server_verification" class="error-text">{{ errors.server_verification }}</p>
              </div>

              <!-- Barcode Select -->
              <div v-show="!settings.barcode_pull" class="setting-field">
                <label class="md-typescale-body-large">Barcode</label>
                <md-outlined-select
                    v-model="settings.barcode"
                    :disabled="settings.barcode_pull"
                    @change="onSettingChange"
                >
                  <md-select-option :value="null">
                    <div slot="headline">-- Select Barcode --</div>
                  </md-select-option>
                  <md-select-option
                      v-for="choice in barcodeChoices"
                      :key="`barcode-${choice.id}`"
                      :value="Number(choice.id)"
                  >
                    <div slot="headline">{{ choice.display }}</div>
                  </md-select-option>
                </md-outlined-select>
                <p v-if="errors.barcode" class="error-text">{{ errors.barcode }}</p>
              </div>
            </div>

            <!-- Auto-save indicator -->
            <transition name="fade">
              <div v-if="isSaving" class="auto-save-indicator">
                <md-icon>sync</md-icon>
                <span class="md-typescale-body-small">Saving changes...</span>
              </div>
            </transition>
          </div>
        </div>

        <!-- Add Barcode Section -->
        <div class="add-barcode-section">
          <div class="section-header">
            <md-icon>add</md-icon>
            <h2 class="md-typescale-headline-small">Add New Barcode</h2>
          </div>

          <form class="form-section" novalidate @submit.prevent="addBarcode">
            <md-outlined-text-field
                v-model="newBarcode"
                :error="!!errors.newBarcode"
                :error-text="errors.newBarcode"
                label="Barcode"
                placeholder="Enter barcode"
                @input="clearError('newBarcode')"
                @keyup.enter="addBarcode()"
            >
              <md-icon slot="leading-icon">qr_code</md-icon>
            </md-outlined-text-field>

            <!-- Scanner Toggle -->
            <md-outlined-button
                class="primary-button"
                type="button"
                @click="toggleScanner"
            >
              <md-icon slot="icon">{{ showScanner ? 'videocam_off' : 'videocam' }}</md-icon>
              {{ showScanner ? 'Hide Scanner' : 'Scan Barcode' }}
            </md-outlined-button>

            <!-- Scanner Section -->
            <transition name="fade">
              <div v-show="showScanner" class="scanner-section">
                <md-outlined-select
                    v-if="cameras.length > 1"
                    v-model="selectedCameraId"
                    class="camera-select"
                    label="Select Camera"
                >
                  <md-select-option
                      v-for="device in cameras"
                      :key="device.deviceId"
                      :value="device.deviceId"
                  >
                    <div slot="headline">{{ device.label }}</div>
                  </md-select-option>
                </md-outlined-select>

                <div class="scanner-card">
                  <div class="video-wrapper">
                    <video
                        ref="videoRef"
                        autoplay
                        muted
                        playsinline
                        webkit-playsinline
                    ></video>
                    <div v-if="scanning" class="scanning-overlay"></div>
                  </div>
                  <div class="scanner-status">
                    <md-icon>info</md-icon>
                    <span class="md-typescale-body-small">{{ scannerStatus }}</span>
                  </div>
                </div>
              </div>
            </transition>

            <md-filled-button class="primary-button" type="submit">
              <md-icon slot="icon">add</md-icon>
              Add Barcode
            </md-filled-button>
          </form>
        </div>


        <!-- Barcodes List Section -->
        <div class="barcodes-section">
          <div class="section-header">
            <md-icon>list</md-icon>
            <h2 class="md-typescale-headline-small">Your Barcodes</h2>
          </div>

          <div v-if="barcodes.length > 0" class="barcodes-grid">
            <div v-for="barcode in barcodes" :key="barcode.id" class="barcode-card">
              <div class="barcode-info">
                <div class="barcode-header">
                  <md-icon class="barcode-icon">
                    {{ barcode.barcode_type === 'DynamicBarcode' ? 'dynamic_feed' : 'code' }}
                  </md-icon>
                  <div class="barcode-details">
                    <h3 class="md-typescale-title-medium">
                      {{ barcode.barcode_type === 'DynamicBarcode' ? 'Dynamic Barcode' : 'Static Barcode' }}
                    </h3>
                    <p class="md-typescale-body-medium barcode-number">
                      ending with {{ barcode.barcode.slice(-4) }}
                    </p>
                  </div>
                </div>

                <div v-if="barcode.usage_count > 0" class="usage-info">
                  <div class="usage-stat">
                    <md-icon>analytics</md-icon>
                    <span class="md-typescale-body-small">
                      Used {{ barcode.usage_count }} time{{ barcode.usage_count > 1 ? 's' : '' }}
                    </span>
                  </div>
                  <div v-if="barcode.last_used" class="last-used">
                    <md-icon>schedule</md-icon>
                    <span class="md-typescale-body-small">
                      Last: {{ formatDate(barcode.last_used) }}
                    </span>
                  </div>
                </div>
              </div>

              <md-outlined-button
                  class="delete-button"
                  @click="deleteBarcode(barcode.id)"
              >
                <md-icon slot="icon">delete</md-icon>
                Delete
              </md-outlined-button>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-content">
              <md-icon class="empty-icon">qr_code_scanner</md-icon>
              <h3 class="md-typescale-headline-small">No barcodes yet</h3>
              <p class="md-typescale-body-medium">Add your first barcode using the form above.</p>
            </div>
          </div>
        </div>

        <!-- Back Link -->
        <div class="nav-section">
          <md-divider></md-divider>
          <p class="md-typescale-body-medium nav-text">
            <router-link class="nav-link" to="/">
              <md-icon>arrow_back</md-icon>
              Back to Dashboard
            </router-link>
          </p>
        </div>
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <md-dialog ref="confirmDialog" :open="showConfirmDialog" @close="showConfirmDialog = false">
      <div slot="headline">
        <md-icon>delete</md-icon>
        Confirm Deletion
      </div>
      <form slot="content" method="dialog">
        <p class="md-typescale-body-medium">Are you sure you want to delete this barcode? This action cannot be
          undone.</p>
      </form>
      <div slot="actions">
        <md-text-button @click="showConfirmDialog = false">Cancel</md-text-button>
        <md-filled-button class="confirm-button" @click="confirmDelete">
          <md-icon slot="icon">delete</md-icon>
          Delete
        </md-filled-button>
      </div>
    </md-dialog>
  </div>
</template>

<script setup>
import {nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {useApi} from '@/composables/useApi';
import '@/styles/auth-shared.css';

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
  barcode_pull: false,
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
      barcode_pull: false,
      server_verification: false,
      barcode: null
    };
    barcodeChoices.value = [];

    // Set choices first
    barcodeChoices.value = data.settings.barcode_choices || [];

    // Then set settings with proper type conversion
    await nextTick(); // Wait for choices to be rendered

    settings.value = {
      barcode_pull: Boolean(data.settings.barcode_pull),
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
async function deleteBarcode(barcodeId) {
  barcodeToDelete.value = barcodeId;
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

// setting change handler
function onSettingChange() {
  // clear barcode when pull is enabled, to avoid user selecting barcode then enabling pull, causing barcode to be cleared
  if (settings.value.barcode_pull) {
    settings.value.barcode = null;
  }

  // debounce logic, 800ms delay to avoid frequent api calls
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }

  saveTimeout = setTimeout(() => {
    autoSaveSettings();
  }, 800);
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

// Watch for barcode pull changes to clear barcode selection
watch(() => settings.value.barcode_pull, (newValue) => {
  if (newValue) {
    settings.value.barcode = null;
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
/* Page-specific styles for BarcodeDashboard.vue */
/* All common styles are now in @/styles/auth-shared.css */

.camera-select {
  margin-bottom: 16px;
  width: 100%;
}

.auto-save-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(25, 118, 210, 0.1);
  border-radius: 8px;
  color: rgb(25, 118, 210);
  margin-top: 16px;
}

.auto-save-indicator md-icon {
  animation: spin 1s linear infinite;
  font-size: 16px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments for the dashboard */
@media (max-width: 800px) {
  .settings-grid,
  .barcodes-grid {
    grid-template-columns: 1fr;
  }
}

</style> 