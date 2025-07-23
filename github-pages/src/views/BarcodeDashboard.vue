<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 800px; width: 100%;">
      <h3 class="text-center mb-4 fw-semibold">Barcode Dashboard</h3>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <!-- Dashboard Content -->
      <div v-else>
        <!-- Flash Messages -->
        <div v-if="message" class="mb-4">
          <div :class="`alert alert-${messageType} alert-dismissible fade show`" role="alert">
            {{ message }}
            <button type="button" class="btn-close" @click="message = ''" aria-label="Close"></button>
          </div>
        </div>

        <!-- Settings Form -->
        <div class="mb-4">
          <h5 class="mb-3 fw-semibold">Barcode Settings</h5>
          <form @submit.prevent="updateSettings" novalidate>
            <div class="row g-3">
              <!-- Pull Setting -->
              <div class="col-md-4">
                <label for="barcode-pull" class="form-label">Barcode Pull</label>
                <select 
                  id="barcode-pull" 
                  v-model="settings.barcode_pull" 
                  class="form-control"
                  :disabled="isUserGroup"
                  @change="onPullSettingChange"
                >
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
                <div v-if="errors.barcode_pull" class="invalid-feedback d-block">
                  {{ errors.barcode_pull }}
                </div>
              </div>

              <!-- Server Verification -->
              <div class="col-md-4">
                <label for="server-verification" class="form-label">Server Verification</label>
                <select 
                  id="server-verification" 
                  v-model="settings.server_verification" 
                  class="form-control"
                >
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
                <div v-if="errors.server_verification" class="invalid-feedback d-block">
                  {{ errors.server_verification }}
                </div>
              </div>

              <!-- Barcode Select -->
              <div class="col-md-4" v-show="!settings.barcode_pull">
                <label for="barcode-select" class="form-label">Barcode</label>
                <select 
                  id="barcode-select" 
                  v-model="settings.barcode" 
                  class="form-control"
                  :disabled="settings.barcode_pull"
                >
                  <option :value="null">-- Select Barcode --</option>
                  <option 
                    v-for="choice in barcodeChoices" 
                    :key="choice.id" 
                    :value="choice.id"
                  >
                    {{ choice.display }}
                  </option>
                </select>
                <div v-if="errors.barcode" class="invalid-feedback d-block">
                  {{ errors.barcode }}
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary w-100 py-2 mt-3">
              Save Settings
            </button>
          </form>
        </div>

        <hr class="my-4" />

        <!-- Add Barcode Form -->
        <div class="mb-4">
          <h5 class="mb-3 fw-semibold">Add New Barcode</h5>
          <form @submit.prevent="addBarcode" novalidate>
            <div class="mb-3">
              <label for="new-barcode" class="form-label">Barcode</label>
              <input 
                id="new-barcode"
                v-model="newBarcode" 
                type="text" 
                class="form-control"
                placeholder="Enter barcode"
                required
              />
              <div v-if="errors.newBarcode" class="invalid-feedback d-block">
                {{ errors.newBarcode }}
              </div>
            </div>

            <!-- Barcode Scanner Section -->
            <div class="mb-3">
              <button 
                type="button" 
                @click="toggleScanner"
                class="btn btn-outline-secondary w-100 py-2"
              >
                {{ showScanner ? 'Hide Scanner' : 'Scan Barcode' }}
              </button>
              
              <transition name="fade">
                <div v-show="showScanner" class="scanner-container mt-3">
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
                  <div class="text-center mt-3">
                    <small class="text-muted">
                      <span>{{ scannerStatus }}</span>
                    </small>
                  </div>
                </div>
              </transition>
            </div>

            <button type="submit" class="btn btn-primary w-100 py-2">
              Add Barcode
            </button>
          </form>
        </div>

        <hr class="my-4" />

        <div class="mb-4">
          <button @click="$router.push('/')" class="btn btn-primary w-100 py-2">
            Back to Home
          </button>
        </div>

        <hr class="my-4" />

        <!-- Barcodes List -->
        <div>
          <h5 class="mb-3 fw-semibold">Barcodes</h5>
          <div v-if="barcodes.length > 0" class="row g-3">
            <div v-for="barcode in barcodes" :key="barcode.id" class="col-12">
              <div class="card border-0 bg-light">
                <div class="card-body d-flex justify-content-between align-items-center py-3">
                  <div class="flex-grow-1">
                    <h6 class="mb-1 fw-semibold">
                      {{ barcode.barcode_type === 'DynamicBarcode' ? 'Dynamic Barcode' : 'Static Barcode' }}
                    </h6>
                    <small class="text-muted">ending with {{ barcode.barcode.slice(-4) }}</small>
                    <div v-if="barcode.usage_count > 0" class="mt-1">
                      <small class="text-muted">
                        Used {{ barcode.usage_count }} time{{ barcode.usage_count > 1 ? 's' : '' }}
                        <span v-if="barcode.last_used">
                          - Last: {{ formatDate(barcode.last_used) }}
                        </span>
                      </small>
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <button 
                      @click="deleteBarcode(barcode.id)"
                      class="btn btn-sm btn-outline-danger"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center text-muted py-4">
            <div class="bg-light rounded p-4">
              <p class="mb-0">No barcodes yet.</p>
              <small class="text-muted">Add your first barcode using the form above.</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useApi } from '@/composables/useApi';

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

// Load dashboard data
async function loadDashboard() {
  try {
    loading.value = true;
    const data = await apiGetBarcodeDashboard();
    
    settings.value = {
      barcode_pull: data.settings.barcode_pull,
      server_verification: data.settings.server_verification,
      barcode: data.settings.barcode
    };
    
    barcodes.value = data.barcodes;
    barcodeChoices.value = data.settings.barcode_choices;
    isUserGroup.value = data.is_user_group;
    isSchoolGroup.value = data.is_school_group;
    
  } catch (error) {
    showMessage('Failed to load dashboard: ' + error.message, 'danger');
  } finally {
    loading.value = false;
  }
}

// Update settings
async function updateSettings() {
  try {
    errors.value = {};
    const response = await apiUpdateBarcodeSettings(settings.value);
    
    if (response.status === 'success') {
      showMessage(response.message, 'success');
      // Update choices from response
      if (response.settings && response.settings.barcode_choices) {
        barcodeChoices.value = response.settings.barcode_choices;
      }
    }
  } catch (error) {
    if (error.message.includes('400') && error.errors) {
      errors.value = error.errors;
    } else {
      showMessage('Failed to update settings: ' + error.message, 'danger');
    }
  }
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
    if (error.message.includes('400') && error.errors) {
      errors.value.newBarcode = error.errors.barcode?.[0] || 'Invalid barcode';
    } else {
      showMessage('Failed to add barcode: ' + error.message, 'danger');
    }
  }
}

// Delete barcode
async function deleteBarcode(barcodeId) {
  if (!confirm('Delete this barcode?')) {
    return;
  }
  
  try {
    const response = await apiDeleteBarcode(barcodeId);
    
    if (response.status === 'success') {
      showMessage(response.message, 'success');
      // Reload dashboard to get updated data
      await loadDashboard();
    }
  } catch (error) {
    showMessage('Failed to delete barcode: ' + error.message, 'danger');
  }
}

// Handle pull setting change
function onPullSettingChange() {
  if (settings.value.barcode_pull) {
    settings.value.barcode = null;
  }
}

// Scanner functions
async function toggleScanner() {
  if (showScanner.value) {
    stopScanner();
    showScanner.value = false;
  } else {
    showScanner.value = true;
    await nextTick();
    startScanner();
  }
}

async function startScanner() {
  try {
    scanning.value = true;
    scannerStatus.value = 'Initializing scanner...';
    
    // Dynamically import ZXing library
    const { BrowserMultiFormatReader } = await import('@zxing/library');
    codeReader = new BrowserMultiFormatReader();
    
    // Start scanning
    scannerStatus.value = 'Position the barcode within the camera view';
    
    await codeReader.decodeFromVideoDevice(
      undefined,
      videoRef.value,
      (result, error) => {
        if (result) {
          newBarcode.value = result.getText();
          showMessage('Barcode scanned successfully!', 'success');
          stopScanner();
          showScanner.value = false;
        }
        
        if (error && error.name !== 'NotFoundException') {
          console.error('Scanner error:', error);
        }
      }
    );
  } catch (error) {
    console.error('Failed to start scanner:', error);
    scannerStatus.value = 'Failed to access camera';
    scanning.value = false;
  }
}

function stopScanner() {
  if (codeReader) {
    codeReader.reset();
    codeReader = null;
  }
  scanning.value = false;
  scannerStatus.value = 'Position the barcode within the camera view';
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
});
</script>

<style scoped>
/* Scanner styles */
.scanner-container {
  background: #fff;
  padding: 15px;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  overflow: hidden;
}

.video-wrapper {
  position: relative;
  width: 100%;
  max-width: 320px;
  height: 240px;
  margin: 0 auto;
  border-radius: 0.25rem;
  overflow: hidden;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
}

.video-wrapper video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  border-radius: calc(0.25rem - 1px);
  background-color: #000;
}

.scanning-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  bottom: 10px;
  border: 2px solid rgba(0, 123, 255, 0.8);
  border-radius: 0.25rem;
  pointer-events: none;
  animation: scanningPulse 2s infinite;
}

@keyframes scanningPulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .video-wrapper {
    max-width: 280px;
    height: 210px;
  }
}

@media (max-width: 480px) {
  .video-wrapper {
    max-width: 260px;
    height: 195px;
  }
}
</style> 