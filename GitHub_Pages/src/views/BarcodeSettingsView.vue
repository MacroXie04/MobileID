<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Barcode Settings</h3>

      <div v-if="isLoading" class="text-center">Loading...</div>

      <form v-else @submit.prevent="handleSubmit" novalidate>
        <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>

        <div v-if="errors.detail" class="alert alert-danger">{{ errors.detail }}</div>

        <div class="mb-3">
          <label for="barcode_pull" class="form-label">Enable Barcode Pull</label>
          <select v-model="settings.barcode_pull" id="barcode_pull" class="form-select"
                  :disabled="isPullDisabled">
            <option :value="true">Yes</option>
            <option :value="false">No</option>
          </select>
          <small v-if="isPullDisabled" class="form-text text-muted">You have no barcodes; Barcode
            Pull is required.</small>
        </div>

        <div class="mb-3">
          <label for="barcode" class="form-label">Active Barcode</label>
          <select v-model="settings.barcode" id="barcode" class="form-select"
                  :disabled="isBarcodeSelectDisabled" :class="{'is-invalid': errors.barcode}">
            <option :value="null">-- None --</option>
            <option v-for="bc in availableBarcodes" :key="bc.id" :value="bc.id">
              {{ bc.barcode_type }} ending with **{{ bc.barcode.slice(-4) }}**
            </option>
          </select>
          <small v-if="settings.barcode_pull" class="form-text text-muted">Automatically select
            barcode by Barcode Pull.</small>
          <div v-if="errors.barcode" class="invalid-feedback">{{ errors.barcode[0] }}</div>
        </div>

        <div class="mb-3">
          <label for="server_verification" class="form-label">Server Verification</label>
          <select v-model="settings.server_verification" id="server_verification"
                  class="form-select">
            <option :value="true">Yes</option>
            <option :value="false">No</option>
          </select>
        </div>

        <div class="mb-4">
          <label for="timestamp_verification" class="form-label">Timestamp Verification</label>
          <select v-model="settings.timestamp_verification" id="timestamp_verification"
                  class="form-select">
            <option :value="true">Yes</option>
            <option :value="false">No</option>
          </select>
        </div>

        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-primary w-100 py-2" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : 'Save Settings' }}
          </button>
          <router-link to="/" class="btn btn-secondary">Back to Home</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref, watch} from 'vue';
import apiClient from '@/api';

// --- State ---
const settings = reactive({
  barcode_pull: true,
  barcode: null,
  server_verification: false,
  timestamp_verification: true,
});
const availableBarcodes = ref([]);
const errors = ref({});
const successMessage = ref('');
const isLoading = ref(true);
const isSubmitting = ref(false);

// --- Computed properties for dynamic UI logic ---
const hasNoBarcodes = computed(() => availableBarcodes.value.length === 0);
const isPullDisabled = computed(() => hasNoBarcodes.value);
const isBarcodeSelectDisabled = computed(() => settings.barcode_pull || hasNoBarcodes.value);

// --- Methods ---
const fetchSettings = async () => {
  isLoading.value = true;
  try {
    const {data} = await apiClient.get('/barcode_settings/');
    Object.assign(settings, data);
    availableBarcodes.value = data.available_barcodes;

    // 如果用户没有 barcode，强制开启 pull
    if (hasNoBarcodes.value) {
      settings.barcode_pull = true;
    }

  } catch (err) {
    console.error("Failed to load settings:", err);
    errors.value = {detail: "Could not load settings."};
  } finally {
    isLoading.value = false;
  }
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  errors.value = {};
  successMessage.value = '';

  const payload = {...settings};
  if (payload.barcode_pull) {
    payload.barcode = null;
  }

  try {
    await apiClient.patch('/barcode_settings/', payload);
    successMessage.value = 'Settings saved successfully!';
  } catch (err) {
    if (err.response?.status === 400) {
      errors.value = err.response.data;
    } else {
      errors.value = {detail: "An unexpected error occurred."};
    }
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(fetchSettings);

watch(() => settings.barcode_pull, (isPullEnabled) => {
  if (isPullEnabled) {
    settings.barcode = null;
  }
});
</script>
