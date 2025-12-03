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
          <md-filled-button ref="submitBtn" :disabled="loading" class="submit-button" type="submit">
            <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
            <md-icon v-if="!loading" slot="icon">login</md-icon>
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </md-filled-button>
        </form>

        <!-- Register Link -->
        <div class="auth-footer">
          <md-divider></md-divider>
          <p class="md-typescale-body-medium footer-text">
            New to MobileID?
            <router-link class="auth-link" to="/register">Create an account</router-link>
          </p>
          <p class="md-typescale-body-small footer-text privacy-link">
            <router-link to="/privacy" class="privacy-link-text">Privacy Policy</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useLoginViewSetup } from './LoginView.setup.js';

const {
  formData,
  loading,
  showPassword,
  submitBtn,
  errors,
  clearError,
  validateField,
  handleSubmit,
} = useLoginViewSetup();
</script>
