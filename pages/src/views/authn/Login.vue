<template>
  <div class="auth-container">
    <!-- Decorative Background -->
    <div class="auth-background">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <!-- Main Content -->
    <main class="auth-main">
      <div class="auth-card md-card md-rounded-xl">
        <!-- Login Form -->
        <form class="auth-form" novalidate @submit.prevent="handleSubmit">
          <div class="form-fields">
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
              <md-icon-button 
                slot="trailing-icon" 
                type="button" 
                @click="showPassword = !showPassword"
              >
                <md-icon>{{ showPassword ? 'visibility_off' : 'visibility' }}</md-icon>
              </md-icon-button>
            </md-outlined-text-field>
          </div>

          <!-- Error Message -->
          <transition name="slide-up">
            <div v-if="errors.general" class="md-banner md-banner-error">
              <md-icon>error_outline</md-icon>
              <span class="md-typescale-body-medium">{{ errors.general }}</span>
            </div>
          </transition>

          <!-- Submit Button -->
          <md-filled-button 
            ref="submitBtn" 
            :disabled="loading" 
            class="submit-button" 
            type="submit"
          >
            <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
            <md-icon v-else slot="icon">login</md-icon>
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </md-filled-button>
          <md-text-button type="button" class="submit-button" :disabled="passkeyBusy" @click="signInWithPasskey">
            <md-circular-progress v-if="passkeyBusy" indeterminate></md-circular-progress>
            <md-icon v-else slot="icon">key</md-icon>
            {{ passkeyBusy ? 'Waiting for device...' : 'Sign in with passkey' }}
          </md-text-button>
        </form>

        <!-- Register Link -->
        <div class="auth-footer">
          <md-divider></md-divider>
          <p class="md-typescale-body-medium footer-text">
            New to MobileID?
            <router-link class="auth-link" to="/register">Create an account</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {login, passkeyAuthOptions, passkeyAuthVerify} from '@/api/auth.js';
import {useRouter} from 'vue-router';

const router = useRouter();
const formData = reactive({username: '', password: ''});
const errors = reactive({});
const loading = ref(false);
const showPassword = ref(false);
const iconBtn = ref(null);
const submitBtn = ref(null);
const passkeyBusy = ref(false);

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
      errors.general = 'Invalid credentials. Please check your username and password.';
    }
  } catch (err) {
    console.error('Login error:', err);
    errors.general = 'Network error. Please check your connection and try again.';
  } finally {
    loading.value = false;
  }
}

function b64urlToArrayBuffer(value) {
  if (value instanceof ArrayBuffer) return value;
  if (value instanceof Uint8Array) return value.buffer;
  if (Array.isArray(value)) return new Uint8Array(value).buffer;
  if (typeof value !== 'string') return new TextEncoder().encode(String(value)).buffer;
  try {
    const padding = '='.repeat((4 - (value.length % 4)) % 4);
    const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(base64);
    const buffer = new ArrayBuffer(raw.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < raw.length; ++i) view[i] = raw.charCodeAt(i);
    return buffer;
  } catch (e) {
    return new TextEncoder().encode(value).buffer;
  }
}

function arrayBufferToB64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  const base64 = btoa(binary).replace(/=+$/g, '');
  return base64.replace(/\+/g, '-').replace(/\//g, '_');
}

async function signInWithPasskey() {
  if (passkeyBusy.value) return;
  passkeyBusy.value = true;
  try {
    const {success, publicKey, message} = await passkeyAuthOptions(formData.username || undefined);
    if (!success) throw new Error(message || 'Failed to start passkey auth');

    const requestOptions = {...publicKey};
    requestOptions.challenge = b64urlToArrayBuffer(publicKey.challenge);
    if (Array.isArray(publicKey.allowCredentials)) {
      requestOptions.allowCredentials = publicKey.allowCredentials.map(c => ({
        ...c,
        id: b64urlToArrayBuffer(c.id)
      }));
    }

    const assertion = await navigator.credentials.get({publicKey: requestOptions});
    if (!assertion) throw new Error('User aborted');

    const credential = {
      id: assertion.id,
      type: assertion.type,
      rawId: arrayBufferToB64url(assertion.rawId),
      response: {
        clientDataJSON: arrayBufferToB64url(assertion.response.clientDataJSON),
        authenticatorData: arrayBufferToB64url(assertion.response.authenticatorData),
        signature: arrayBufferToB64url(assertion.response.signature),
        userHandle: assertion.response.userHandle ? arrayBufferToB64url(assertion.response.userHandle) : null,
      },
    };

    const verifyRes = await passkeyAuthVerify(credential);
    if (verifyRes.success) {
      await router.push('/');
    } else {
      errors.general = verifyRes.message || 'Passkey sign-in failed';
    }
  } catch (e) {
    console.error('Passkey sign-in error:', e);
    errors.general = e.message || 'Passkey sign-in failed';
  } finally {
    passkeyBusy.value = false;
  }
}


</script>

<style scoped>
/* Page-specific styles for Login.vue - minimal overrides only */

/* Auth Container Backgrounds */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--md-sys-spacing-6);
  position: relative;
  overflow: hidden;
  background: var(--md-sys-color-surface-container-lowest);
}

/* Decorative Background Shapes */
.auth-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.shape-1 {
  width: 400px;
  height: 400px;
  background: var(--md-sys-color-primary);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.shape-2 {
  width: 300px;
  height: 300px;
  background: var(--md-sys-color-secondary);
  bottom: -150px;
  left: -100px;
  animation: float 25s ease-in-out infinite reverse;
}

.shape-3 {
  width: 250px;
  height: 250px;
  background: var(--md-sys-color-tertiary);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float 30s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  33% {
    transform: translateY(-20px) rotate(120deg);
  }
  66% {
    transform: translateY(20px) rotate(240deg);
  }
}

/* Auth Card Overrides */
.auth-main {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
}

.auth-card {
  padding: var(--md-sys-spacing-12) var(--md-sys-spacing-10);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background-color: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
}

/* Logo Container */
.logo-container {
  width: 72px;
  height: 72px;
  margin: 0 auto var(--md-sys-spacing-6);
  background: var(--md-sys-color-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.logo-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%
  );
  transform: translateX(-100%);
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  to {
    transform: translateX(100%);
  }
}

.logo-icon {
  font-size: 40px;
  color: var(--md-sys-color-on-primary-container);
  z-index: 1;
}

/* Form Specific */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-6);
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-5);
}

/* Loading state opacity */
.auth-card:has(.submit-button[disabled]) {
  pointer-events: none;
}

.auth-card:has(.submit-button[disabled]) .form-fields {
  opacity: 0.7;
}

/* Link underline animation */
.auth-link {
  position: relative;
  text-decoration: none;
  color: var(--md-sys-color-primary);
  font-weight: 500;
  transition: color 0.2s ease;
}

.auth-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--md-sys-color-primary);
  transform: scaleX(0);
  transition: transform 0.2s ease;
}

.auth-link:hover::after {
  transform: scaleX(1);
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(10px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* Submit button full width */
.submit-button {
  width: 100%;
}

/* Footer spacing */
.auth-footer {
  margin-top: var(--md-sys-spacing-8);
}

.auth-footer md-divider {
  margin-bottom: var(--md-sys-spacing-6);
}

.footer-text {
  text-align: center;
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
}

/* Responsive */
@media (max-width: 599px) {
  .auth-container {
    padding: var(--md-sys-spacing-4);
  }
  
  .auth-card {
    padding: var(--md-sys-spacing-8) var(--md-sys-spacing-6);
    border-radius: var(--md-sys-shape-corner-large);
  }
  
  .logo-container {
    width: 64px;
    height: 64px;
  }
  
  .logo-icon {
    font-size: 32px;
  }
  
  .shape {
    filter: blur(100px);
  }
}
</style>