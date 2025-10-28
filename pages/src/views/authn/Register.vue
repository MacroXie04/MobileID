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

        <!-- Registration Form -->
        <form class="auth-form" novalidate @submit.prevent="handleSubmit">
          <!-- Avatar Upload Section -->
          <div class="avatar-section">
            <div class="avatar-upload-wrapper md-flex md-items-center md-gap-4 md-p-3 md-rounded-lg">
              <div class="avatar-container" @click="selectImage">
                <img :src="getAvatarSrc()" alt="Profile" class="avatar-image">
                <div class="avatar-overlay">
                  <md-icon>photo_camera</md-icon>
                </div>
              </div>
              <div class="avatar-text">
                <p class="md-typescale-label-large md-m-0">Profile Photo</p>
                <p class="md-typescale-body-small md-m-0 md-mt-1">Optional • Click to upload</p>
              </div>
            </div>
            <input
              ref="fileInput"
              accept="image/jpeg,image/jpg,image/png"
              class="hidden-input"
              type="file"
              @change="handleFileSelect"
            >
            <transition name="slide-up">
              <div v-if="errors.user_profile_img" class="md-banner md-banner-error md-mt-2">
                <md-icon>error</md-icon>
                <span>{{ errors.user_profile_img[0] || errors.user_profile_img }}</span>
              </div>
            </transition>
          </div>

          <!-- Form Fields -->
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
              v-model="formData.name"
              :error="!!errors.name"
              :error-text="errors.name"
              label="Full Name"
              @blur="validateField('name')"
              @input="clearError('name')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">badge</md-icon>
            </md-outlined-text-field>

            <md-outlined-text-field
              v-model="formData.information_id"
              :error="!!errors.information_id"
              :error-text="errors.information_id"
              label="Information ID"
              @blur="validateField('information_id')"
              @input="clearError('information_id')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">fingerprint</md-icon>
            </md-outlined-text-field>

            <md-outlined-text-field
              v-model="formData.password1"
              :error="!!errors.password1"
              :error-text="errors.password1"
              :type="showPassword1 ? 'text' : 'password'"
              label="Password"
              @blur="validateField('password1')"
              @input="clearError('password1')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">lock</md-icon>
              <md-icon-button slot="trailing-icon" type="button" @click="showPassword1 = !showPassword1">
                <md-icon>{{ showPassword1 ? 'visibility_off' : 'visibility' }}</md-icon>
              </md-icon-button>
            </md-outlined-text-field>

            <md-outlined-text-field
              v-model="formData.password2"
              :error="!!errors.password2"
              :error-text="errors.password2"
              :type="showPassword2 ? 'text' : 'password'"
              label="Confirm Password"
              @blur="validateField('password2')"
              @input="clearError('password2')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">lock</md-icon>
              <md-icon-button slot="trailing-icon" type="button" @click="showPassword2 = !showPassword2">
                <md-icon>{{ showPassword2 ? 'visibility_off' : 'visibility' }}</md-icon>
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
          <md-filled-button :disabled="loading" class="submit-button" type="submit">
            <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
            <md-icon v-else slot="icon">how_to_reg</md-icon>
            {{ loading ? 'Creating Account...' : 'Create Account' }}
          </md-filled-button>
        </form>

        <!-- Login Link -->
        <div class="auth-footer">
          <md-divider></md-divider>
          <p class="md-typescale-body-medium footer-text">
            Already have an account?
            <router-link class="auth-link" to="/login">Sign in instead</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>

  <!-- Cropper Dialog -->
  <md-dialog ref="cropperDialog" :open="showCropper" class="cropper-dialog" @close="handleDialogClose">
    <div slot="headline">
      <md-icon>crop</md-icon>
      Crop Your Photo
    </div>
    <form slot="content" class="cropper-content" method="dialog">
      <div class="cropper-main">
        <div ref="cropperContainer" class="cropper-container">
          <img v-show="!cropperLoading" ref="cropperImage" alt="Image to crop" class="cropper-image">
          <div v-if="cropperLoading" class="cropper-loading">
            <md-circular-progress indeterminate></md-circular-progress>
            <p class="md-typescale-body-medium">Loading image...</p>
          </div>
        </div>
        <div class="cropper-sidebar">
          <div class="cropper-preview-section">
            <h3 class="md-typescale-title-small">Preview</h3>
            <div ref="cropperPreview" class="cropper-preview"></div>
            <p class="md-typescale-body-small preview-text">Final result (128×128)</p>
          </div>

          <div class="cropper-controls">
            <h3 class="md-typescale-title-small">Controls</h3>

            <!-- Zoom Controls -->
            <div class="control-group">
              <label class="md-typescale-body-small">Zoom</label>
              <div class="zoom-controls">
                <md-icon-button :disabled="cropperLoading" @click="zoomOut">
                  <md-icon>zoom_out</md-icon>
                </md-icon-button>
                <input
                    v-model="zoomLevel"
                    :disabled="cropperLoading"
                    class="zoom-slider"
                    max="3"
                    min="0.1"
                    step="0.1"
                    type="range"
                    @input="handleZoomChange"
                >
                <md-icon-button :disabled="cropperLoading" @click="zoomIn">
                  <md-icon>zoom_in</md-icon>
                </md-icon-button>
              </div>
              <div class="zoom-value md-typescale-body-small">{{ Math.round(zoomLevel * 100) }}%</div>
            </div>
          </div>
        </div>
      </div>

      <div class="cropper-tips md-typescale-body-small">
        <md-icon>info</md-icon>
        <span class="tips-desktop">Drag to move • Scroll to zoom • Drag corners to resize crop area</span>
        <span class="tips-mobile">Drag to move • Pinch to zoom • Drag corners to resize</span>
      </div>
    </form>
    <div slot="actions">
      <md-text-button @click="cancelCrop">Cancel</md-text-button>
      <md-text-button :disabled="cropperLoading" @click="resetCrop">
        <md-icon slot="icon">refresh</md-icon>
        Reset
      </md-text-button>
      <md-filled-button :disabled="cropperLoading || applyingCrop" @click="applyCrop">
        <md-circular-progress v-if="applyingCrop" indeterminate></md-circular-progress>
        <md-icon v-else slot="icon">check</md-icon>
        {{ applyingCrop ? 'Processing...' : 'Apply' }}
      </md-filled-button>
    </div>
  </md-dialog>
</template>

<script setup>
import {nextTick, onUnmounted, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {register} from '@/api/auth.js';
import {useRegisterValidation} from '@/composables/useRegisterValidation.js';
import {useImageCropper} from '@/composables/useImageCropper.js';
import {validateImageFile, createImageObjectURL} from '@/utils/imageUtils.js';

const router = useRouter();

// Refs
const fileInput = ref(null);
const cropperDialog = ref(null);

// State
const loading = ref(false);
const formData = ref({
  username: '',
  name: '',
  information_id: '',
  password1: '',
  password2: '',
  user_profile_img_base64: ''
});
const avatarFile = ref(null);
const avatarPreviewUrl = ref('');
const showPassword1 = ref(false);
const showPassword2 = ref(false);

// Validation composable
const {errors, clearError, validateField: validateSingleField, validateForm, setServerErrors, setGeneralError} = useRegisterValidation();

// Image cropper composable with advanced controls
const {
  cropperImage,
  cropperPreview,
  showCropper,
  cropperLoading,
  applyingCrop,
  zoomLevel,
  initializeCropper,
  resetCrop,
  zoomIn,
  zoomOut,
  handleZoomChange,
  applyCrop: applyCropBase,
  closeCropper
} = useImageCropper({
  targetWidth: 128,
  targetHeight: 128,
  quality: 0.7,
  enableAdvancedControls: true
});

// Methods
const getAvatarSrc = () => {
  return avatarPreviewUrl.value || '/images/avatar_placeholder.png';
};

const selectImage = () => {
  fileInput.value?.click();
};

// Wrapper function to pass formData to validation
function validateField(field) {
  validateSingleField(field, formData.value);
}

const handleFileSelect = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate file
  const validation = validateImageFile(file);
  if (!validation.success) {
    errors.user_profile_img = [validation.error];
    fileInput.value.value = '';
    return;
  }

  // Clear previous errors
  delete errors.user_profile_img;

  // Create temporary URL and initialize cropper
  const tempUrl = URL.createObjectURL(file);
  await initializeCropper(tempUrl);
};

// Apply crop wrapper
const applyCrop = async () => {
  try {
    const result = await applyCropBase({maxBase64Length: 30000});

    if (result) {
      avatarFile.value = result.file;
      formData.value.user_profile_img_base64 = result.base64;

      // Update preview URL
      if (avatarPreviewUrl.value) {
        URL.revokeObjectURL(avatarPreviewUrl.value);
      }
      avatarPreviewUrl.value = result.previewUrl;
    }

    closeCropper();
    fileInput.value.value = '';
  } catch (error) {
    console.error('Failed to apply crop:', error);
    errors.user_profile_img = ['Failed to process image. Please try again.'];
  }
};

const cancelCrop = () => {
  closeCropper();
  fileInput.value.value = '';
};

const handleDialogClose = () => {
  closeCropper();
  fileInput.value.value = '';
};

const handleSubmit = async () => {
  if (loading.value) return;

  // Validate form
  if (!validateForm(formData.value)) {
    return;
  }

  loading.value = true;
  Object.keys(errors).forEach(key => delete errors[key]);

  try {
    // Register user
    const response = await register(formData.value);

    if (!response.success) {
      // Handle API errors
      if (response.errors) {
        setServerErrors(response.errors);
      } else {
        setGeneralError(response.detail || response.message || 'Registration failed. Please check your information.');
      }
      return;
    }

    // Success - avatar was already included in registration data as base64
    router.push('/');

  } catch (error) {
    console.error('Registration error:', error);

    // Try to parse error message for API errors
    try {
      const errorData = JSON.parse(error.message);
      if (errorData.message) {
        setGeneralError(errorData.message);
      } else if (errorData.errors) {
        setServerErrors(errorData.errors);
      } else {
        setGeneralError('Registration failed. Please try again.');
      }
    } catch (parseError) {
      setGeneralError('Network error. Please check your connection and try again.');
    }
  } finally {
    loading.value = false;
  }
};

// Cleanup
onUnmounted(() => {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
  }
  // Cropper cleanup is handled by the composable
});
</script>

<style scoped>
/* Page-specific styles for Register.vue - minimal overrides only */

/* Auth Container (reuse from Login) */
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

/* Auth Main - wider for registration */
.auth-main {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
}

/* Auth Card */
.auth-card {
  padding: var(--md-sys-spacing-12) var(--md-sys-spacing-10);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background-color: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-large);
  box-shadow: var(--md-elevation-2);
}

/* Logo Container - secondary color for registration */
.logo-container {
  width: 72px;
  height: 72px;
  margin: 0 auto var(--md-sys-spacing-6);
  background: var(--md-sys-color-secondary-container);
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
  color: var(--md-sys-color-on-secondary-container);
  z-index: 1;
}

/* Avatar Section */
.avatar-section {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-3);
  align-items: center;
}

.avatar-upload-wrapper {
  cursor: pointer;
  transition: background-color 0.2s ease;
  width: 100%;
}

.avatar-upload-wrapper:hover {
  background: var(--md-sys-color-surface-container);
}

.avatar-container {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--md-sys-spacing-1);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.avatar-container:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay md-icon {
  color: white;
  font-size: 28px;
}

.avatar-text {
  flex: 1;
  color: var(--md-sys-color-on-surface-variant);
}

.hidden-input {
  display: none;
}

/* Form Structure */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-6);
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-4);
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

/* Link styling */
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

/* Loading state */
.auth-card:has(.submit-button[disabled]) {
  pointer-events: none;
}

.auth-card:has(.submit-button[disabled]) .form-fields {
  opacity: 0.7;
}

/* Page-specific responsive adjustments */
@media (max-width: 599px) {
  .auth-container {
    padding: var(--md-sys-spacing-4);
  }
  
  .auth-card {
    padding: var(--md-sys-spacing-8) var(--md-sys-spacing-6);
    border-radius: var(--md-sys-shape-corner-large);
  }
  
  .avatar-upload-wrapper {
    flex-direction: column;
    text-align: center;
  }
  
  .avatar-container {
    width: 100px;
    height: 100px;
  }
  
  .logo-container {
    width: 64px;
    height: 64px;
  }
  
  .logo-icon {
    font-size: 32px;
  }
  
  .form-fields {
    gap: var(--md-sys-spacing-3);
  }
  
  .shape {
    filter: blur(100px);
  }
}

/* Cropper Dialog Styles */
.cropper-dialog {
  --md-dialog-container-max-width: min(90vw, 800px);
  --md-dialog-container-max-height: min(85vh, 600px);
}

.cropper-content {
  padding: 0;
  overflow: hidden;
}

.cropper-main {
  display: flex;
  gap: var(--md-sys-spacing-4);
  min-height: 400px;
}

.cropper-container {
  flex: 1;
  min-width: 300px;
  height: 400px;
  position: relative;
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
}

.cropper-image {
  max-width: 100%;
  max-height: 100%;
  display: block;
}

.cropper-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--md-sys-spacing-4);
  color: var(--md-sys-color-on-surface-variant);
}

.cropper-sidebar {
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-5);
  padding: var(--md-sys-spacing-4);
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
  overflow-y: auto;
}

.cropper-preview-section h3,
.cropper-controls h3 {
  margin: 0 0 var(--md-sys-spacing-3) 0;
  color: var(--md-sys-color-on-surface);
}

.cropper-preview {
  width: 128px;
  height: 128px;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 50%;
  margin: 0 auto var(--md-sys-spacing-2);
  background: var(--md-sys-color-surface);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-text {
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.control-group {
  margin-bottom: var(--md-sys-spacing-5);
}

.control-group label {
  display: block;
  margin-bottom: var(--md-sys-spacing-2);
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
}

.zoom-value {
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: var(--md-sys-spacing-1);
  font-weight: 500;
}

.zoom-slider {
  flex: 1;
  height: 4px;
  background: var(--md-sys-color-outline-variant);
  border-radius: 2px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.zoom-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--md-sys-color-primary);
  border-radius: 50%;
  cursor: pointer;
}

.zoom-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--md-sys-color-primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.cropper-tips {
  padding: var(--md-sys-spacing-4);
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
  margin-top: var(--md-sys-spacing-4);
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  color: var(--md-sys-color-on-surface-variant);
}

.cropper-tips md-icon {
  --md-icon-size: 18px;
  color: var(--md-sys-color-primary);
}

.tips-mobile {
  display: none;
}

.tips-desktop {
  display: inline;
}

/* Mobile-first responsive design */
@media (max-width: 599px) {
  .cropper-dialog {
    --md-dialog-container-max-width: 95vw;
    --md-dialog-container-max-height: 90vh;
  }

  .cropper-main {
    flex-direction: column;
    min-height: auto;
    gap: var(--md-sys-spacing-3);
  }

  .cropper-container {
    min-width: unset;
    height: 280px;
    order: 1;
  }

  .cropper-sidebar {
    width: 100%;
    order: 2;
    padding: var(--md-sys-spacing-3);
    gap: var(--md-sys-spacing-4);
  }

  .cropper-preview {
    width: 96px;
    height: 96px;
  }

  .control-group {
    margin-bottom: var(--md-sys-spacing-4);
  }

  .zoom-controls {
    gap: var(--md-sys-spacing-1);
  }

  .zoom-slider {
    height: 6px;
  }

  .tips-mobile {
    display: inline;
  }

  .tips-desktop {
    display: none;
  }
}

/* Tablet adjustments */
@media (min-width: 600px) and (max-width: 904px) {
  .cropper-dialog {
    --md-dialog-container-max-width: 85vw;
    --md-dialog-container-max-height: 80vh;
  }

  .cropper-container {
    min-width: 350px;
    height: 350px;
  }

  .cropper-sidebar {
    width: 220px;
  }
}

/* Desktop optimization */
@media (min-width: 905px) {
  .cropper-main {
    min-height: 450px;
  }

  .cropper-container {
    height: 450px;
  }
}

/* Cropper.js style overrides */
:deep(.cropper-container) {
  font-family: inherit;
}

:deep(.cropper-view-box) {
  border: 2px solid var(--md-sys-color-primary);
  border-radius: 50%;
}

:deep(.cropper-face) {
  background-color: var(--md-sys-color-surface-container);
  opacity: 0.1;
}

:deep(.cropper-line) {
  background-color: var(--md-sys-color-primary);
  opacity: 0.8;
}

:deep(.cropper-point) {
  background-color: var(--md-sys-color-primary);
  opacity: 0.9;
  width: 8px;
  height: 8px;
}
</style>