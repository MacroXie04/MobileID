<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Login</h3>

      <form novalidate @submit.prevent="handleLogin">

        <!-- Account disabled error (highest priority) -->
        <div v-if="errors.account_disabled" class="alert alert-danger">
          <i class="fas fa-ban me-2"></i>
          Your account is disabled. Please contact administrator for assistance.
        </div>

        <!-- Account locked error -->
        <div v-else-if="errors.is_locked" class="alert alert-danger">
          <i class="fas fa-lock me-2"></i>
          Your account is locked. Please try again later.
        </div>

        <!-- Failed login attempts warning -->
        <div v-else-if="errors.failed_attempts" class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Warning: {{ errors.failed_attempts }} failed login attempts. 
          {{ errors.attempts_remaining }} attempts remaining before your account is locked.
        </div>

        <!-- General error messages (including throttling) -->
        <div v-else-if="errors.detail" class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>
          {{ errors.detail }}
        </div>

        <div class="mb-3">
          <label class="form-label" for="username">Username</label>
          <input
              id="username"
              v-model="username"
              :class="{ 'is-invalid': errors.username }"
              class="form-control"
              placeholder="Enter your username"
              required
              type="text"
          />
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username[0] }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label" for="password">Password</label>
          <input
              id="password"
              v-model="password"
              :class="{ 'is-invalid': errors.password }"
              class="form-control"
              placeholder="Enter your password"
              required
              type="password"
          />
          <div v-if="errors.password" class="invalid-feedback">
            {{ errors.password[0] }}
          </div>
        </div>

        <button 
          class="btn btn-primary w-100 py-2" 
          type="submit" 
          :disabled="isLoading"
        >
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status"></span>
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <div class="text-center mt-2">
        <p>Don't have an account?
          <router-link to="/register">Register here</router-link>
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue';
import apiClient from '@/api';
import {useRouter} from 'vue-router';

const username = ref('');
const password = ref('');
const errors = ref({});
const isLoading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  errors.value = {};
  isLoading.value = true;

  try {
    const response = await apiClient.post('token/', {
      username: username.value,
      password: password.value,
    });

    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    // Check user status after successful login
    try {
      const userResponse = await apiClient.get('/api/me/');
      const userData = userResponse.data;
      
      // Check the comprehensive account status
      if (userData.account_status) {
        const accountStatus = userData.account_status;
        
        // Handle different account statuses
        switch (accountStatus.status) {
          case 'disabled':
            // User account is disabled
            console.log('User account is disabled:', accountStatus.message);
            await router.push('/account-disabled');
            return;
            
          case 'locked':
            // User account is locked
            console.log('User account is locked:', accountStatus.message);
            if (accountStatus.locked_until) {
              const lockTime = new Date(accountStatus.locked_until);
              const now = new Date();
              if (lockTime > now) {
                // Account is still locked, redirect to disabled page
                await router.push('/account-disabled');
                return;
              }
            }
            break;
        }
      } else {
        // Fallback to old is_active check for backward compatibility
        if (userData.is_active === false) {
          console.log('User account is inactive (legacy check)');
          await router.push('/account-disabled');
          return;
        }
      }
      
      // Store user status in localStorage for components to access
      localStorage.setItem('user_status', JSON.stringify(userData.account_status || { status: 'unknown' }));
      localStorage.setItem('user_profile', JSON.stringify(userData.userprofile || {}));
      
    } catch (userErr) {
      console.error('Error checking user status:', userErr);
    }

    await router.push('/');

  } catch (err) {
    console.error('Login error:', err);
    
    if (err.response) {
      const errorData = err.response.data;
      const status = err.response.status;
      
      // Check if account is disabled
      if (errorData.account_disabled) {
        console.log('Account is disabled, redirecting to account disabled page');
        await router.push('/account-disabled');
        return;
      }
      
      // Handle different error statuses
      if (status === 429) {
        // Rate limiting/throttling error
        errors.value = {
          detail: errorData.detail || 'Too many login attempts. Please wait before trying again.'
        };
        console.log('Throttling error set:', errors.value);
      } else if (status === 400 || status === 401) {
        // Authentication errors
        errors.value = errorData;
        console.log('Authentication error set:', errors.value);
      } else {
        // Other server errors
        errors.value = {
          detail: errorData.detail || 'Server error occurred. Please try again later.'
        };
        console.log('Server error set:', errors.value);
      }
    } else if (err.request) {
      // Network error
      errors.value = {
        detail: 'Network error. Please check your connection and try again.'
      };
    } else {
      // Other errors
      errors.value = {
        detail: 'An unexpected error occurred. Please try again.'
      };
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.invalid-feedback {
  display: block;
}
</style>
