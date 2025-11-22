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
            <div
              class="avatar-upload-wrapper md-flex md-items-center md-gap-4 md-p-3 md-rounded-lg"
            >
              <div class="avatar-container" @click="selectImage">
                <img :src="getAvatarSrc()" alt="Profile" class="avatar-image" />
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
            />
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
              <md-icon-button
                slot="trailing-icon"
                type="button"
                @click="showPassword1 = !showPassword1"
              >
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
              <md-icon-button
                slot="trailing-icon"
                type="button"
                @click="showPassword2 = !showPassword2"
              >
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
            <md-icon v-if="!loading" slot="icon">how_to_reg</md-icon>
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
  <md-dialog
    ref="cropperDialog"
    :open="showCropper"
    class="cropper-dialog"
    @close="handleDialogClose"
  >
    <div slot="headline">
      <md-icon>crop</md-icon>
      Crop Your Photo
    </div>
    <form slot="content" class="cropper-content" method="dialog">
      <div class="cropper-main">
        <div ref="cropperContainer" class="cropper-container">
          <img
            v-show="!cropperLoading"
            ref="cropperImage"
            alt="Image to crop"
            class="cropper-image"
          />
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
                />
                <md-icon-button :disabled="cropperLoading" @click="zoomIn">
                  <md-icon>zoom_in</md-icon>
                </md-icon-button>
              </div>
              <div class="zoom-value md-typescale-body-small">
                {{ Math.round(zoomLevel * 100) }}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="cropper-tips md-typescale-body-small">
        <md-icon>info</md-icon>
        <span class="tips-desktop"
          >Drag to move • Scroll to zoom • Drag corners to resize crop area</span
        >
        <span class="tips-mobile">Drag to move • Pinch to zoom • Drag corners to resize</span>
      </div>
    </form>
    <div slot="actions">
      <div>
        <md-text-button @click="cancelCrop">Cancel</md-text-button>
        <md-text-button :disabled="cropperLoading" @click="resetCrop">
          <md-icon slot="icon">refresh</md-icon>
          Reset
        </md-text-button>
        <md-filled-button :disabled="cropperLoading || applyingCrop" @click="applyCrop">
          <md-circular-progress v-if="applyingCrop" indeterminate></md-circular-progress>
          <md-icon v-if="!applyingCrop" slot="icon">check</md-icon>
          {{ applyingCrop ? 'Processing...' : 'Apply' }}
        </md-filled-button>
      </div>
    </div>
  </md-dialog>
</template>

<script setup>
import { onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { register } from '@/api/auth.js';
import { useRegisterValidation } from '@/composables/auth/useRegisterValidation.js';
import { useImageCropper } from '@/composables/user/useImageCropper.js';
import { validateImageFile } from '@/utils/user/imageUtils.js';
import '@/assets/css/auth-merged.css';

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
  user_profile_img_base64: '',
});
const avatarFile = ref(null);
const avatarPreviewUrl = ref('');
const showPassword1 = ref(false);
const showPassword2 = ref(false);

// Validation composable
const {
  errors,
  clearError,
  validateField: validateSingleField,
  validateForm,
  setServerErrors,
  setGeneralError,
} = useRegisterValidation();

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
  closeCropper,
} = useImageCropper({
  targetWidth: 128,
  targetHeight: 128,
  quality: 0.7,
  enableAdvancedControls: true,
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
    const result = await applyCropBase({ maxBase64Length: 30000 });

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
  Object.keys(errors).forEach((key) => delete errors[key]);

  try {
    // Register user
    const response = await register(formData.value);

    if (!response.success) {
      // Handle API errors
      if (response.errors) {
        setServerErrors(response.errors);
      } else {
        setGeneralError(
          response.detail ||
            response.message ||
            'Registration failed. Please check your information.'
        );
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
    } catch (_parseError) {
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
