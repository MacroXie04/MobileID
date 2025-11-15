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
import {login} from '@/api/auth.js';
import {ApiError} from '@/api/client.js';
import {useRouter} from 'vue-router';
import {useLoginValidation} from '@/composables/auth/useLoginValidation.js';
import {usePasskeyAuth} from '@/composables/auth/usePasskeyAuth.js';
import '@/assets/css/auth-merged.css';

const router = useRouter();
const formData = reactive({username: '', password: ''});
const loading = ref(false);
const showPassword = ref(false);
const iconBtn = ref(null);
const submitBtn = ref(null);

// Use validation composable
const {errors, clearError, validateField: validateSingleField, validateForm, setGeneralError} = useLoginValidation();

// Use passkey authentication composable
const {passkeyBusy, error: passkeyError, signInWithPasskey: passkeySignIn} = usePasskeyAuth();

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

// Wrapper function to pass formData to validation
function validateField(field) {
  validateSingleField(field, formData);
}

async function handleSubmit() {
  if (!validateForm(formData)) return;
  loading.value = true;
  try {
    const res = await login(formData.username, formData.password);
    if (res.message === 'Login successful') {
      // Prefer SPA navigation to preserve app state
      await router.push('/');
    } else {
      setGeneralError('Unable to sign in. Please try again.');
    }
  } catch (err) {
    console.error('Login error:', err);
    if (err instanceof ApiError) {
      setGeneralError(err.data?.detail || 'Invalid username or password.');
    } else {
      setGeneralError('Network error. Please check your connection and try again.');
    }
  } finally {
    loading.value = false;
  }
}

async function signInWithPasskey() {
  const success = await passkeySignIn(formData.username);
  if (success) {
    await router.push('/');
  } else if (passkeyError.value) {
    setGeneralError(passkeyError.value);
  }
}
</script>