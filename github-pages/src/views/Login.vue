<template>
  <div class="page-container">
    <div class="page-card">
      <!-- Header -->
      <div class="page-header">
        <p class="md-typescale-body-large subtitle">
          Enter your credentials to access your account
        </p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleSubmit" novalidate class="form-fields">
        <md-outlined-text-field
          label="Username"
          v-model="formData.username"
          :error="!!errors.username"
          :error-text="errors.username"
          @input="clearError('username')"
          @blur="validateField('username')"
          @keyup.enter="!loading && handleSubmit()"
        >
          <md-icon slot="leading-icon">person</md-icon>
        </md-outlined-text-field>

        <md-outlined-text-field
          :type="showPassword ? 'text' : 'password'"
          label="Password"
          v-model="formData.password"
          :error="!!errors.password"
          :error-text="errors.password"
          @input="clearError('password')"
          @blur="validateField('password')"
          @keyup.enter="!loading && handleSubmit()"
        >
          <md-icon slot="leading-icon">lock</md-icon>
        </md-outlined-text-field>

        <!-- Error Message -->
        <div v-if="errors.general" class="error-banner">
          <md-icon>error_outline</md-icon>
          <span class="md-typescale-body-medium">{{ errors.general }}</span>
        </div>

        <!-- Submit Button -->
        <md-filled-button ref="submitBtn" type="submit" :disabled="loading" class="primary-button">
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </md-filled-button>
      </form>

      <!-- Divider and Register Link -->
      <div class="nav-section">
        <md-divider></md-divider>
        <p class="md-typescale-body-medium nav-text">
          Don't have an account?
          <router-link to="/register" class="nav-link">Create one now</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { login } from '@/api/auth';
import { useRouter } from 'vue-router';
import '@/styles/auth-shared.css';

const router = useRouter();
const formData = reactive({ username: '', password: '' });
const errors = reactive({});
const loading = ref(false);
const showPassword = ref(false);
const iconBtn = ref(null);
const submitBtn = ref(null);

onMounted(() => {
  if (iconBtn.value) {
    const internalBtn = iconBtn.value.shadowRoot?.querySelector('button');
    if (internalBtn) {
      internalBtn.id = 'password-toggle';
      internalBtn.type = 'button';
    }
  }
  if (submitBtn.value) {
    const internalBtn = submitBtn.value.shadowRoot?.querySelector('button');
    if (internalBtn) internalBtn.id = 'login-submit';
  }
});

function clearError(field) {
  delete errors[field];
  if (field === 'username' || field === 'password') delete errors.general;
}

function validateField(field) {
  clearError(field);
  if (field === 'username') {
    if (!formData.username.trim()) errors.username = 'Username is required';
    else if (formData.username.length < 3) errors.username = 'Username must be at least 3 characters';
  }
  if (field === 'password') {
    if (!formData.password) errors.password = 'Password is required';
    else if (formData.password.length < 6) errors.password = 'Password must be at least 6 characters';
  }
}

function validateForm() {
  let isValid = true;
  Object.keys(errors).forEach(key => delete errors[key]);
  validateField('username');
  validateField('password');
  if (errors.username || errors.password) isValid = false;
  return isValid;
}

async function handleSubmit() {
  if (!validateForm()) return;
  loading.value = true;
  try {
    const res = await login(formData.username, formData.password);
    if (res.message === 'Login successful') {
      location.href = '/';
    } else {
      errors.general = res.detail || res.message || 'Login failed. Please check your credentials.';
    }
  } catch (err) {
    console.error('Login error:', err);
    errors.general = 'Network error. Please check your connection and try again.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* Page-specific styles for Login.vue */
</style>