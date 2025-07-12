<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Login</h3>

      <form novalidate @submit.prevent="handleLogin">

        <div v-if="errors.detail && !errors.is_locked && !errors.failed_attempts" class="alert alert-danger">
          {{ errors.detail }}
        </div>

        <div v-if="errors.failed_attempts && !errors.is_locked" class="alert alert-warning">
          Warning: {{ errors.failed_attempts }} failed login attempts. 
          {{ errors.attempts_remaining }} attempts remaining before your account is locked.
        </div>

        <div v-if="errors.is_locked" class="alert alert-danger">
          Your account is locked. Please try again later.
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

        <button class="btn btn-primary w-100 py-2" type="submit">Login</button>
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
const router = useRouter();

const handleLogin = async () => {
  errors.value = {};

  try {
    const response = await apiClient.post('token/', {
      username: username.value,
      password: password.value,
    });

    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    // Check user status after successful login
    try {
      const userResponse = await apiClient.get('/me/');
      if (userResponse.data.is_active === false) {
        // User is disabled, redirect to account disabled page
        await router.push('/account-disabled');
        return;
      }
    } catch (userErr) {
      console.error('Error checking user status:', userErr);
    }

    await router.push('/');

  } catch (err) {
    if (err.response && (err.response.status === 400 || err.response.status === 401)) {
      errors.value = err.response.data;
    } else {
      errors.value = {detail: 'An unexpected error occurred. Please try again.'};
    }
    console.error(err);
  }
};
</script>

<style scoped>
.invalid-feedback {
  display: block;
}
</style>
