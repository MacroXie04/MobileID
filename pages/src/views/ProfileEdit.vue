<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h3 class="md-typescale-title-medium md-m-0">Edit Profile</h3>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Auto-save Status Toast -->
    <transition name="slide-down">
      <div v-if="autoSaveStatus.show" :class="['message-toast md-banner', autoSaveStatus.type === 'success' ? 'md-banner-success' : 'md-banner-error']">
        <md-icon>{{ autoSaveStatus.type === 'success' ? 'check_circle' : 'error' }}</md-icon>
        <span class="md-typescale-body-medium">{{ autoSaveStatus.message }}</span>
        <md-icon-button @click="autoSaveStatus.show = false">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Success Message Toast -->
    <transition name="slide-down">
      <div v-if="successMessage" class="message-toast md-banner md-banner-success" style="top: 160px;">
        <md-icon>check_circle</md-icon>
        <span class="md-typescale-body-medium">{{ successMessage }}</span>
        <md-icon-button @click="successMessage = ''">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="md-content">
      <section class="md-card md-max-w-xl">
        <form class="md-form" novalidate @submit.prevent="handleSubmit">
          <!-- Avatar Upload Section -->
          <div class="avatar-section md-mb-8">
            <h2 class="md-typescale-headline-small section-title md-mb-6">Profile Photo</h2>
            
            <div class="avatar-upload-container md-flex md-items-center md-gap-8">
              <div class="avatar-section-center">
                <div class="avatar-wrapper md-avatar-xl" @click="selectImage">
                  <img :src="getAvatarSrc()" alt="Profile" class="avatar-image">
                  <div class="avatar-overlay">
                    <md-icon>photo_camera</md-icon>
                    <span class="md-typescale-label-medium">Change Photo</span>
                  </div>
                </div>
                
                <div class="avatar-info">
                  <p class="md-typescale-body-medium md-m-0">Click to upload a new profile photo</p>
                  <p class="md-typescale-body-small md-m-0 md-mt-1">JPG or PNG • Max 5MB • Recommended: Square image</p>
                </div>
              </div>
            </div>
            
            <input
              ref="fileInput"
              accept="image/jpeg,image/jpg,image/png"
              class="hidden-input"
              type="file"
              @change="handleFileSelect"
            >
            
            <transition name="fade">
              <div v-if="errors.user_profile_img" class="md-banner md-banner-error md-mt-4">
                <md-icon>error</md-icon>
                <span>{{ errors.user_profile_img }}</span>
              </div>
            </transition>
          </div>

          <md-divider></md-divider>

          <!-- Personal Information Section -->
          <div class="info-section md-mt-8">
            <h2 class="md-typescale-headline-small section-title md-mb-6">Personal Information</h2>
            
            <div class="md-form-field">
              <md-outlined-text-field
                v-model="formData.name"
                :error="!!errors.name"
                :error-text="errors.name"
                label="Full Name"
                @input="handleFieldChange('name')"
                @keyup.enter="!loading && handleSubmit()"
              >
                <md-icon slot="leading-icon">badge</md-icon>
              </md-outlined-text-field>

              <md-outlined-text-field
                v-model="formData.information_id"
                :error="!!errors.information_id"
                :error-text="errors.information_id"
                label="Information ID"
                @input="handleFieldChange('information_id')"
                @keyup.enter="!loading && handleSubmit()"
              >
                <md-icon slot="leading-icon">fingerprint</md-icon>
              </md-outlined-text-field>
            </div>
          </div>

          <md-divider></md-divider>

          <!-- Passkey Management Section -->
          <div class="info-section md-mt-8">
            <h2 class="md-typescale-headline-small section-title md-mb-6">Passkey</h2>
            <div class="md-flex md-items-center md-justify-between md-gap-4">
              <div class="md-typescale-body-medium">
                <md-icon class="md-mr-2">{{ hasPasskey ? 'key' : 'key_off' }}</md-icon>
                {{ hasPasskey ? 'Passkey registered' : 'No passkey registered' }}
              </div>
              <md-filled-button type="button" :disabled="passkeyBusy" @click="registerPasskey">
                <md-circular-progress v-if="passkeyBusy" indeterminate></md-circular-progress>
                <md-icon v-else slot="icon">{{ hasPasskey ? 'sync' : 'key' }}</md-icon>
                {{ hasPasskey ? 'Replace Passkey' : 'Register Passkey' }}
              </md-filled-button>
            </div>
            <p class="md-typescale-body-small md-text-on-surface-variant md-mt-2">
              Passkeys let you sign in without a password using your device or security key.
            </p>
          </div>

          <!-- Auto-save Status Indicator -->
          <div class="auto-save-status md-mt-4 md-p-3 md-rounded-lg md-bg-surface-container-low">
            <div class="md-flex md-items-center md-gap-2">
              <md-icon v-if="autoSaving" class="auto-save-icon">
                <md-circular-progress indeterminate></md-circular-progress>
              </md-icon>
              <md-icon v-else-if="lastSaved" class="auto-save-icon md-text-primary">
                check_circle
              </md-icon>
              <md-icon v-else class="auto-save-icon md-text-on-surface-variant">
                schedule
              </md-icon>
              <span class="md-typescale-body-small">
                {{ getAutoSaveStatusText() }}
              </span>
            </div>
          </div>

          <!-- Error Banner -->
          <transition name="fade">
            <div v-if="errors.general" class="md-banner md-banner-error md-mt-6">
              <md-icon>error_outline</md-icon>
              <span class="md-typescale-body-medium">{{ errors.general }}</span>
            </div>
          </transition>
        </form>
      </section>
    </main>
  </div>

  <!-- Cropper Dialog -->
  <md-dialog ref="cropperDialog" :open="showCropper" class="cropper-dialog" @close="handleDialogClose">
    <div slot="headline">
      <md-icon>crop</md-icon>
      Crop Your Photo
    </div>
    <form slot="content" class="cropper-content" method="dialog">
      <div ref="cropperContainer" class="cropper-container md-rounded-lg">
        <img ref="cropperImage" alt="Image to crop" class="cropper-image">
      </div>
      <div class="cropper-tips md-typescale-body-small md-p-4 md-mt-4 md-rounded-lg md-text-center">
        Drag to reposition • Scroll to zoom • Double-click to reset
      </div>
    </form>
    <div slot="actions">
      <md-text-button @click="cancelCrop">Cancel</md-text-button>
      <md-text-button @click="resetCrop">
        <md-icon slot="icon">refresh</md-icon>
        Reset
      </md-text-button>
      <md-filled-button @click="applyCrop">
        <md-icon slot="icon">check</md-icon>
        Apply
      </md-filled-button>
    </div>
  </md-dialog>

</template>

<script setup>
import {onMounted, onUnmounted, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {getUserProfile, updateUserProfile} from '@/api/auth';
import {baseURL} from '@/config';
import {useImageCropper} from '@/composables/useImageCropper.js';
import {usePasskeyRegistration} from '@/composables/usePasskeyRegistration.js';
import {useAutoSave} from '@/composables/useAutoSave.js';
import {validateImageFile, fileToBase64} from '@/utils/imageUtils.js';

const router = useRouter();

// Refs
const fileInput = ref(null);
const cropperDialog = ref(null);

// State
const loading = ref(false);
const formData = ref({
  name: '',
  information_id: ''
});
const avatarFile = ref(null);
const avatarPreviewUrl = ref('');
const errors = ref({});
const successMessage = ref('');
const hasPasskey = ref(false);
const originalData = ref({});

// Image cropper composable (simple version without advanced controls)
const {
  cropperImage,
  showCropper,
  cropperLoading,
  applyingCrop,
  initializeCropper,
  resetCrop,
  applyCrop: applyCropBase,
  closeCropper
} = useImageCropper({
  targetWidth: 256,
  targetHeight: 256,
  quality: 0.9,
  enableAdvancedControls: false
});

// Passkey registration composable
const {
  passkeyBusy,
  error: passkeyError,
  registerPasskey: registerPasskeyBase
} = usePasskeyRegistration();

// Auto-save composable
const {
  autoSaving,
  lastSaved,
  hasChanges,
  autoSaveStatus,
  triggerAutoSave,
  getStatusText: getAutoSaveStatusText,
  hideToast
} = useAutoSave(autoSaveChanges, {
  debounceMs: 1500
});

// Methods
const getAvatarSrc = () => {
  return avatarPreviewUrl.value || '/images/avatar_placeholder.png';
};

const selectImage = () => {
  fileInput.value?.click();
};

const clearError = (field) => {
  delete errors.value[field];
  if (field !== 'general') {
    delete errors.value.general;
  }
};

const handleFileSelect = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate file
  const validation = validateImageFile(file, {
    allowedTypes: /^image\/(jpe?g|png)$/i,
    maxSizeMB: 5
  });

  if (!validation.success) {
    errors.value.user_profile_img = validation.error;
    fileInput.value.value = '';
    return;
  }

  // Clear previous errors
  delete errors.value.user_profile_img;

  // Create temporary URL and initialize cropper
  const tempUrl = URL.createObjectURL(file);
  await initializeCropper(tempUrl);
};

const applyCrop = async () => {
  try {
    const result = await applyCropBase();

    if (result) {
      avatarFile.value = result.file;

      // Update preview URL
      if (avatarPreviewUrl.value) {
        URL.revokeObjectURL(avatarPreviewUrl.value);
      }
      avatarPreviewUrl.value = result.previewUrl;

      // Trigger auto-save for avatar change
      triggerAutoSave();
    }

    closeCropper();
    fileInput.value.value = '';
  } catch (error) {
    console.error('Failed to apply crop:', error);
    errors.value.user_profile_img = 'Failed to process image. Please try again.';
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

const handleFieldChange = (field) => {
  clearError(field);
  triggerAutoSave();
};

// Auto-save changes function
async function autoSaveChanges() {
  // Prepare data for auto-save
  const profileData = {
    name: formData.value.name,
    information_id: formData.value.information_id
  };

  // Check if text fields have changed
  const textFieldsChanged = JSON.stringify(profileData) !== JSON.stringify(originalData.value);

  // Add base64 avatar if there's a new one
  if (avatarFile.value) {
    profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
  }

  // Only auto-save if data has actually changed
  if (!textFieldsChanged && !avatarFile.value) {
    return {success: false};
  }

  const response = await updateUserProfile(profileData);

  if (response.success) {
    // Update original data to match current data
    originalData.value = {
      name: formData.value.name,
      information_id: formData.value.information_id
    };

    // Clear avatar file after successful save
    if (avatarFile.value) {
      avatarFile.value = null;
    }

    return {success: true, message: 'Profile auto-saved successfully'};
  } else {
    return {success: false, message: response.message || 'Auto-save failed'};
  }
}

const handleSubmit = async () => {
  if (loading.value) return;

  loading.value = true;
  errors.value = {};

  try {
    // Prepare data including base64 avatar if available
    const profileData = {...formData.value};

    // Add base64 avatar if there's a new one
    if (avatarFile.value) {
      profileData.user_profile_img_base64 = await fileToBase64(avatarFile.value);
    }

    // Update profile with avatar data included
    const response = await updateUserProfile(profileData);
    if (!response.success) {
      if (response.errors) {
        Object.keys(response.errors).forEach(key => {
          if (Array.isArray(response.errors[key])) {
            errors.value[key] = response.errors[key][0];
          } else {
            errors.value[key] = response.errors[key];
          }
        });
      } else {
        errors.value.general = response.message || 'Update failed';
      }
      return;
    }

    // Success - show message then redirect
    successMessage.value = 'Profile updated successfully!';

    // Update original data to match current data
    originalData.value = {
      name: formData.value.name,
      information_id: formData.value.information_id
    };

    setTimeout(() => {
      router.push('/');
    }, 1500);
  } catch (error) {
    console.error('Update error:', error);
    errors.value.general = 'Network error. Please try again.';
  } finally {
    loading.value = false;
  }
};

const loadProfile = async () => {
  try {
    const response = await getUserProfile();
    if (response.success) {
      formData.value = {...response.data};
      if (typeof response.data.has_passkey !== 'undefined') {
        hasPasskey.value = !!response.data.has_passkey;
      }
      
      // Initialize original data for auto-save comparison
      originalData.value = {
        name: response.data.name || '',
        information_id: response.data.information_id || ''
      };

      // Load avatar separately
      try {
        const avatarResponse = await fetch(`${baseURL}/authn/user_img/`, {
          credentials: "include"
        });
        if (avatarResponse.ok) {
          const blob = await avatarResponse.blob();
          avatarPreviewUrl.value = URL.createObjectURL(blob);
        }
      } catch (avatarError) {
        console.log('No avatar found or error loading avatar');
      }
    }
  } catch (error) {
    console.error('Failed to load profile:', error);
    errors.value.general = 'Failed to load profile data';
  }
};

// Passkey registration wrapper
async function registerPasskey() {
  const success = await registerPasskeyBase();
  if (success) {
    hasPasskey.value = true;
    successMessage.value = 'Passkey registered successfully!';
    setTimeout(() => successMessage.value = '', 3000);
  } else if (passkeyError.value) {
    errors.value.general = passkeyError.value;
  }
}

// Cleanup
onUnmounted(() => {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
  }
  // Auto-save and cropper cleanup is handled by composables
});

// Lifecycle
onMounted(() => {
  loadProfile();
});
</script>

<style scoped>
/* Page-specific styles for ProfileEdit.vue - minimal overrides only */

/* Message Toast positioning */
.message-toast {
  position: fixed;
  top: 88px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 600px;
}

/* Card styling aligned to Material 3 */
.md-card {
  background-color: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-large);
  box-shadow: var(--md-elevation-2);
  padding: var(--md-sys-spacing-8);
}

/* Section Title styling */
.section-title {
  color: var(--md-sys-color-on-surface);
}

/* Avatar Section */
.avatar-section-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--md-sys-spacing-4);
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  transition: transform 0.2s ease;
  box-shadow: var(--md-elevation-1);
}

.avatar-wrapper:hover {
  transform: scale(1.05);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
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
  border-radius: 50%;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay md-icon {
  font-size: 32px;
  color: white;
}

.avatar-overlay span {
  color: white;
}

.avatar-info {
  color: var(--md-sys-color-on-surface-variant);
  max-width: 300px;
}

.hidden-input {
  display: none;
}

/* Form fields spacing */
.md-form-field {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-4);
}

/* Cropper Dialog */
.cropper-dialog {
  --md-dialog-container-max-width: min(90vw, 600px);
}

.cropper-content {
  padding: 0;
}

.cropper-container {
  height: 300px;
  background: var(--md-sys-color-surface-container-low);
  overflow: hidden;
}

.cropper-image {
  max-width: 100%;
  display: block;
}

.cropper-tips {
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface-variant);
}

/* Auto-save Status Indicator */
.auto-save-status {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  padding: var(--md-sys-spacing-2) var(--md-sys-spacing-3);
  border-radius: var(--md-sys-shape-small);
  background-color: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface-variant);
  border: 1px solid var(--md-sys-color-outline-variant);
  transition: all 0.2s ease;
}

.auto-save-status:hover {
  background-color: var(--md-sys-color-surface-container);
}

.auto-save-icon {
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auto-save-icon md-circular-progress {
  width: 20px;
  height: 20px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .avatar-upload-container {
    flex-direction: column;
    text-align: center;
  }
  
  .avatar-info {
    text-align: center;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions > * {
    width: 100%;
  }
}

/* Large screen adjustments */
@media (min-width: 769px) {
  .avatar-upload-container {
    justify-content: center;
  }
  
  .avatar-section-center {
    width: 100%;
    max-width: 400px;
  }
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translate(-50%, -100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translate(-50%, -100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}</style> 