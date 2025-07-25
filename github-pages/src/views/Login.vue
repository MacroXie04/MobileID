<template>
  <div class="login-container">
    <div class="login-surface">
      <!-- Header -->
      <div class="login-header">
        <p class="md-typescale-body-large">Enter your credentials to access your account</p>
      </div>

      <form @submit.prevent="handleSubmit" novalidate>
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

        <div v-if="errors.general" class="error-banner">
          <md-icon>error_outline</md-icon>
          <span class="md-typescale-body-medium">{{ errors.general }}</span>
        </div>

        <md-filled-button ref="submitBtn" type="submit" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </md-filled-button>
      </form>

      <md-divider class="divider"></md-divider>

      <div class="register-link md-typescale-body-medium">
        <div class="register-content">
          Don't have an account?
          <router-link to="/register">
            <md-text-button>
              <md-icon slot="icon">person_add</md-icon>
              Create one now
            </md-text-button>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { login } from "@/api/auth";
import { useRouter } from "vue-router";

// Router
const router = useRouter();

// Form data
const formData = reactive({
  username: '',
  password: ''
});

// UI state
const errors = reactive({});
const loading = ref(false);
const showPassword = ref(false);
const rememberMe = ref(false);
const iconBtn = ref(null);
const submitBtn = ref(null);

onMounted(() => {
  if (iconBtn.value) {
    const internalBtn = iconBtn.value.shadowRoot.querySelector('button');
    if (internalBtn) {
      internalBtn.id = 'password-toggle';
      internalBtn.type = 'button';
    }
  }
  if (submitBtn.value) {
    const internalBtn = submitBtn.value.shadowRoot.querySelector('button');
    if (internalBtn) internalBtn.id = 'login-submit';
  }
});

// Clear specific error
function clearError(field) {
  delete errors[field];
  if (field === 'username' || field === 'password') {
    delete errors.general;
  }
}

// Validate specific field
function validateField(field) {
  clearError(field);
  
  switch (field) {
    case 'username':
      if (!formData.username.trim()) {
        errors.username = 'Username is required';
      } else if (formData.username.length < 3) {
        errors.username = 'Username must be at least 3 characters';
      }
      break;
      
    case 'password':
      if (!formData.password) {
        errors.password = 'Password is required';
      } else if (formData.password.length < 6) {
        errors.password = 'Password must be at least 6 characters';
      }
      break;
  }
}

// Validate all fields
function validateForm() {
  let isValid = true;
  
  // Clear previous errors
  Object.keys(errors).forEach(key => delete errors[key]);
  
  // Validate username
  if (!formData.username.trim()) {
    errors.username = 'Username is required';
    isValid = false;
  } else if (formData.username.length < 3) {
    errors.username = 'Username must be at least 3 characters';
    isValid = false;
  }
  
  // Validate password
  if (!formData.password) {
    errors.password = 'Password is required';
    isValid = false;
  } else if (formData.password.length < 6) {
    errors.password = 'Password must be at least 6 characters';
    isValid = false;
  }
  
  return isValid;
}

// Handle form submission
async function handleSubmit() {
  // Validate form
  if (!validateForm()) {
    return;
  }
  
  loading.value = true;
  
  try {
    const res = await login(formData.username, formData.password);
    
    if (res.message === "Login successful") {
      // Redirect to home
      location.href = "/";
    } else {
      // Handle login error
      errors.general = res.detail || res.message || 'Login failed. Please check your credentials.';
    }
  } catch (error) {
    console.error('Login error:', error);
    errors.general = 'Network error. Please check your connection and try again.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background-color: var(--md-sys-color-background);
}

.login-surface {
  width: 100%;
  max-width: 500px;
  padding: 24px;
  border-radius: 28px;
  background-color: var(--md-sys-color-surface);
  border: 2px solid #D1D5DB; /* light gray border for surface */
  box-shadow: none;
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.brand-icon {
  font-size: 48px;
  color: var(--md-sys-color-primary);
  margin-bottom: 16px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.divider {
  margin: 16px 0;
}

.register-link {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.register-content {
  display: flex;
  align-items: center;
  gap: 4px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #fff;
  color: #d32f2f;
  border-radius: 12px;
  margin: 12px 0;
  border: 2px solid #d32f2f;
  font-weight: 500;
}

md-outlined-text-field::part(field),
md-outlined-text-field::part(outline) {
  border: 1.5px solid var(--md-sys-color-outline, #79747E) !important;
  border-radius: 12px !important;
}

md-filled-button::part(button) {
  border: 1.5px solid var(--md-sys-color-outline, #79747E) !important;
  border-radius: 20px !important;
}
</style>
