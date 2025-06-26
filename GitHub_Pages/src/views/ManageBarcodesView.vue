<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Create & Manage Barcode</h3>
      <form @submit.prevent="handleSubmit" novalidate>
        <div v-if="errors.non_field_errors" class="alert alert-danger">{{
            errors.non_field_errors[0]
          }}
        </div>

        <div class="mb-3">
          <label for="source_type" class="form-label">Source Type</label>
          <select v-model="form.source_type" id="source_type" class="form-select">
            <option value="barcode">Barcode</option>
            <option value="session">Session</option>
          </select>
        </div>

        <div class="mb-3">
          <label for="input_value" class="form-label">Input Value</label>
          <input type="text" v-model="form.input_value" id="input_value" class="form-control"
                 :class="{'is-invalid': errors.input_value}">
          <div v-if="errors.input_value" class="invalid-feedback">
            {{ Array.isArray(errors.input_value) ? errors.input_value[0] : errors.input_value }}
          </div>
        </div>

        <!-- Scan Barcode -->
        <div v-if="form.source_type === 'barcode'" class="mb-3">
          <button type="button" @click="toggleScan" class="btn btn-info w-100 py-2">
            {{ isScanning ? 'Cancel Scan' : 'Scan CatCard' }}
          </button>
          <div v-show="isScanning" class="video-container mt-2">
            <video ref="videoElement" style="width: 100%; border: 1px solid #ccc;"></video>
          </div>
        </div>

        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-primary py-2" :disabled="isSubmitting">
            {{ isSubmitting ? 'Submitting...' : 'Submit' }}
          </button>
          <router-link to="/" class="btn btn-secondary">Back to Home</router-link>
        </div>
      </form>

      <!-- Barcode List -->
      <hr class="my-4">
      <h4 class="text-center mb-3">Your Barcodes</h4>
      <div v-if="barcodes.length > 0">
        <ul class="list-group">
          <li v-for="bc in barcodes" :key="bc.id"
              class="list-group-item d-flex justify-content-between align-items-center">
            <span>{{ bc.barcode_type }} Barcode Ending With {{
                bc.barcode.slice(-4)
              }}</span>
            <button @click="handleDelete(bc.id)" class="btn btn-danger btn-sm"
                    :disabled="isDeleting === bc.id">
              {{ isDeleting === bc.id ? '...' : 'Delete' }}
            </button>
          </li>
        </ul>
      </div>
      <p v-else class="text-muted text-center">No barcodes yet.</p>
    </div>
  </div>
</template>

<script setup>
import {onMounted, onUnmounted, reactive, ref, watch} from 'vue';
import apiClient from '@/api';
import {BrowserMultiFormatReader, NotFoundException} from '@zxing/library';

// --- State ---
const form = reactive({source_type: 'barcode', input_value: ''});
const errors = ref({});
const barcodes = ref([]);
const isSubmitting = ref(false);
const isDeleting = ref(null);

// --- Scanner State ---
const isScanning = ref(false);
const videoElement = ref(null);
const codeReader = new BrowserMultiFormatReader();
let stream = null;

// --- Methods ---
const fetchBarcodes = async () => {
  try {
    const {data} = await apiClient.get('/barcodes/');
    barcodes.value = data;
  } catch (err) {
    console.error("Failed to fetch barcodes:", err);
  }
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  errors.value = {};
  try {
    await apiClient.post('/barcodes/', form);
    form.input_value = '';
    await fetchBarcodes();
  } catch (err) {
    if (err.response?.status === 400) {
      errors.value = err.response.data;
    } else {
      console.error("Submission failed:", err);
    }
  } finally {
    isSubmitting.value = false;
  }
};

const handleDelete = async (barcodeId) => {
  if (!confirm('Are you sure you want to delete this barcode?')) return;
  isDeleting.value = barcodeId;
  try {
    await apiClient.delete(`/barcodes/${barcodeId}/`);
    await fetchBarcodes();
  } catch (err) {
    console.error("Failed to delete barcode:", err);
  } finally {
    isDeleting.value = null;
  }
};

// --- Scanner Logic ---
const startScanning = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}});
    videoElement.value.srcObject = stream;
    isScanning.value = true;

    codeReader.decodeFromStream(stream, videoElement.value, (result, err) => {
      if (result) {
        form.input_value = result.getText();
        stopScanning();
      }
      if (err && !(err instanceof NotFoundException)) {
        console.error(err);
      }
    });
  } catch (err) {
    console.error("Could not start scanner:", err);
  }
};

const stopScanning = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  codeReader.reset();
  isScanning.value = false;
  stream = null;
};

const toggleScan = () => {
  isScanning.value ? stopScanning() : startScanning();
};

// --- Lifecycle Hooks ---
onMounted(fetchBarcodes);
onUnmounted(stopScanning);

watch(() => form.source_type, (newVal) => {
  if (newVal !== 'barcode' && isScanning.value) {
    stopScanning();
  }
});
</script>
