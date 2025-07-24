<template>
  <div class="login-container">
    <div class="login-card">

      <!-- Login Form -->
      <form @submit.prevent="handleSubmit" novalidate>
        <!-- Username Field -->
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-user"></i>
            Username
          </label>
          <input 
            v-model="formData.username"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.username }"
            placeholder="Enter your username"
            @input="clearError('username')"
            @blur="validateField('username')"
          />
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username }}
          </div>
        </div>

        <!-- Password Field -->
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-lock"></i>
            Password
          </label>
          <div class="password-input-wrapper">
            <input 
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-control"
              :class="{ 'is-invalid': errors.password }"
              placeholder="Enter your password"
              @input="clearError('password')"
              @blur="validateField('password')"
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
            >
              <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <div v-if="errors.password" class="invalid-feedback">
            {{ errors.password }}
          </div>
        </div>

        <!-- General Error Message -->
        <div v-if="errors.general" class="alert alert-danger">
          <i class="fas fa-exclamation-triangle"></i>
          {{ errors.general }}
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          class="btn btn-primary btn-login"
          :disabled="loading"
        >
          <span v-if="!loading">
            <i class="fas fa-sign-in-alt"></i>
            Sign In
          </span>
          <span v-else>
            <i class="fas fa-spinner fa-spin"></i>
            Signing in...
          </span>
        </button>
      </form>

      <!-- Divider -->
      <div class="divider">
        <span>OR</span>
      </div>

      <!-- Register Link -->
      <div class="register-link">
        <p>
          Don't have an account? 
          <router-link to="/register">Create one now</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
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
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 450px;
  transition: transform 0.3s ease;
}

/* Header Section */
.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-container {
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 60px;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 10px;
}

.login-subtitle {
  color: #666;
  font-size: 16px;
}

/* Form Styling */
.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.form-label i {
  margin-right: 8px;
  color: #667eea;
}

.form-control {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-control.is-invalid {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.form-control.is-invalid:focus {
  box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.1);
}

/* Password Input Wrapper */
.password-input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 8px;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: #333;
}

.password-input-wrapper .form-control {
  padding-right: 48px;
}

/* Error Messages */
.invalid-feedback {
  display: block;
  margin-top: 6px;
  color: #dc3545;
  font-size: 14px;
  font-weight: 500;
}

.alert {
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.alert-danger {
  background-color: #fee;
  color: #c53030;
  border: 1px solid #feb2b2;
}

/* Buttons */
.btn {
  border: none;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-login {
  width: 100%;
  padding: 14px 24px;
  font-size: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.btn-login:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-login:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Divider */
.divider {
  text-align: center;
  margin: 30px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e0e0e0;
}

.divider span {
  background: white;
  padding: 0 16px;
  position: relative;
  color: #666;
  font-size: 14px;
}

/* Social Login */
.social-login {
  margin-bottom: 24px;
}

.btn-social {
  width: 100%;
  padding: 12px 24px;
  background: white;
  border: 2px solid #e0e0e0;
  color: #333;
  font-size: 15px;
}

.btn-social:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.btn-social:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Register Link */
.register-link {
  text-align: center;
  margin-top: 20px;
}

.register-link p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.register-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.register-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on iOS */
  }
}
</style>
