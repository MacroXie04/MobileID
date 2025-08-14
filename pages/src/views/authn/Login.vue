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
      <form class="form-fields" novalidate @submit.prevent="handleSubmit">
        <md-outlined-text-field
            v-model="formData.username"
            :error="!!errors.username"
            :error-text="errors.username"
            label="Username"
            @blur="validateField('username')"
            @input="clearError('username')"
            @keyup.enter="!loading && handleSubmit()"
        >
          <md-icon slot="leading-icon">person</md-icon>
        </md-outlined-text-field>

        <md-outlined-text-field
            v-model="formData.password"
            :error="!!errors.password"
            :error-text="errors.password"
            :type="showPassword ? 'text' : 'password'"
            label="Password"
            @blur="validateField('password')"
            @input="clearError('password')"
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
        <md-filled-button ref="submitBtn" :disabled="loading" class="primary-button unified-button" type="submit">
          {{ loading ? 'Signing in...' : 'Sign In with Password' }}
        </md-filled-button>

        <!-- Passkey Login Option -->
        <div v-if="webAuthnSupported" class="passkey-primary-section">
          <md-filled-button :disabled="passkeyLoading" class="passkey-primary-button unified-button"
                            @click="handlePasskeyLogin">
            <md-icon slot="icon">key</md-icon>
            {{ passkeyLoading ? 'Authenticating...' : 'Sign in with Passkey' }}
          </md-filled-button>
        </div>
      </form>

      <!-- Divider and Register Link -->
      <div class="nav-section">
        <md-divider></md-divider>
        <p class="md-typescale-body-medium nav-text">
          Don't have an account?
          <router-link class="nav-link" to="/register">Create one now</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {login} from '@/api/auth.js';
import {authenticateWithPasskey, isWebAuthnSupported} from '@/api/passkeys.js';
import {useRouter} from 'vue-router';
import '@/styles/auth-shared.css';

const router = useRouter();
const formData = reactive({username: '', password: ''});
const errors = reactive({});
const loading = ref(false);
const passkeyLoading = ref(false);
const showPassword = ref(false);
const iconBtn = ref(null);
const submitBtn = ref(null);
const webAuthnSupported = ref(false);

onMounted(() => {
  // Check WebAuthn support
  webAuthnSupported.value = isWebAuthnSupported();

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
      // Prefer SPA navigation to preserve app state
      await router.push('/');
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

async function handlePasskeyLogin() {
  passkeyLoading.value = true;
  errors.general = '';

  try {
    // Try to authenticate with passkey
    // Don't pass username - let the user select from available passkeys
    const result = await authenticateWithPasskey();

    if (result.success) {
      // Successful login, redirect
      await router.push('/');
    } else {
      errors.general = result.message || 'Passkey authentication failed';
    }
  } catch (error) {
    console.error('Passkey login error:', error);

    // Handle specific errors
    if (error.name === 'NotAllowedError') {
      errors.general = 'Authentication was cancelled or not allowed';
    } else if (error.name === 'InvalidStateError') {
      errors.general = 'No passkey found for this device';
    } else {
      errors.general = 'Passkey authentication failed. Please try password login.';
    }
  } finally {
    passkeyLoading.value = false;
  }
}
</script>

<style scoped>
/* Page-specific styles for Login.vue */
.passkey-primary-section {
  margin: 8px 0 0 0; /* Reduced spacing above the passkey button */
}

.passkey-primary-button {
  width: 100%;
  /* No extra bottom margin here; spacing handled by unified-button */
}

.divider-with-text {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.divider-with-text md-divider {
  flex: 1;
}

.divider-text {
  color: var(--md-sys-color-on-surface-variant);
}

.passkey-button {
  width: 100%;
}

.unified-button {
  width: 100%;
  margin-bottom: 12px; /* Slightly smaller gap between buttons */
}

.unified-button:last-child {
  margin-bottom: 0; /* Remove bottom margin for the last button in the group */
}
</style>