<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h1 class="md-typescale-display-small md-m-0">Edit Profile</h1>
          <p class="md-typescale-body-large md-m-0 md-mt-1">Update your personal information</p>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Success Message Toast -->
    <transition name="slide-down">
      <div v-if="successMessage" class="message-toast md-banner md-banner-success">
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
                @input="clearError('information_id')"
                @keyup.enter="!loading && handleSubmit()"
              >
                <md-icon slot="leading-icon">fingerprint</md-icon>
              </md-outlined-text-field>
            </div>
          </div>

          <!-- Error Banner -->
          <transition name="fade">
            <div v-if="errors.general" class="md-banner md-banner-error md-mt-6">
              <md-icon>error_outline</md-icon>
              <span class="md-typescale-body-medium">{{ errors.general }}</span>
            </div>
          </transition>

          <!-- Form Actions -->
          <div class="form-actions md-flex md-justify-end md-gap-3 md-mt-8">
            <md-outlined-button type="button" @click="router.push('/')">
              Cancel
            </md-outlined-button>
            <md-filled-button type="submit" :disabled="loading">
              <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
              <md-icon v-else slot="icon">save</md-icon>
              {{ loading ? 'Saving...' : 'Save Changes' }}
            </md-filled-button>
          </div>
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
import {nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {getUserProfile, updateUserProfile} from '@/api/auth';
import {baseURL} from '@/config';
import Cropper from 'cropperjs';
import 'cropperjs/dist/cropper.css';

const router = useRouter();

// Refs
const fileInput = ref(null);
const cropperImage = ref(null);
const cropperContainer = ref(null);
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
const cropper = ref(null);
const showCropper = ref(false);
const tempImageUrl = ref('');
const successMessage = ref('');

// Methods
const getAvatarSrc = () => {
  return avatarPreviewUrl.value || '/images/avatar_placeholder.png';
};

const selectImage = () => {
  fileInput.value?.click();
};

// Clear specific error
const clearError = (field) => {
  delete errors.value[field];
  if (field !== 'general') {
    delete errors.value.general;
  }
};

const handleFileSelect = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate file type
  if (!/^image\/(jpe?g|png)$/i.test(file.type)) {
    errors.value.user_profile_img = 'Please select a JPG or PNG image';
    fileInput.value.value = '';
    return;
  }

  // Validate file size
  if (file.size > 5 * 1024 * 1024) {
    errors.value.user_profile_img = 'Image size must be less than 5MB';
    fileInput.value.value = '';
    return;
  }

  // Clear previous errors
  delete errors.value.user_profile_img;

  // Create temporary URL for cropper
  if (tempImageUrl.value) {
    URL.revokeObjectURL(tempImageUrl.value);
  }
  tempImageUrl.value = URL.createObjectURL(file);

  // Initialize cropper
  await initializeCropper();
};

const initializeCropper = async () => {
  showCropper.value = true;

  await nextTick();

  if (!cropperImage.value || !tempImageUrl.value) return;

  // Destroy previous cropper instance
  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }

  // Load image and initialize cropper
  cropperImage.value.onload = () => {
    cropper.value = new Cropper(cropperImage.value, {
      aspectRatio: 1,
      viewMode: 2,
      dragMode: 'move',
      autoCropArea: 0.9,
      restore: false,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: true,
      cropBoxResizable: true,
      toggleDragModeOnDblclick: true,
      minContainerWidth: 300,
      minContainerHeight: 300,
      minCropBoxWidth: 100,
      minCropBoxHeight: 100,
    });
  };

  cropperImage.value.src = tempImageUrl.value;
};

const resetCrop = () => {
  if (cropper.value) {
    cropper.value.reset();
    cropper.value.setDragMode('move');
  }
};

const applyCrop = () => {
  if (!cropper.value) return;

  const canvas = cropper.value.getCroppedCanvas({
    width: 256,
    height: 256,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high'
  });

  canvas.toBlob((blob) => {
    if (blob) {
      // Create file from blob
      avatarFile.value = new File([blob], 'avatar.png', {type: 'image/png'});

      // Update preview
      if (avatarPreviewUrl.value) {
        URL.revokeObjectURL(avatarPreviewUrl.value);
      }
      avatarPreviewUrl.value = URL.createObjectURL(blob);
    }
    closeCropper();
  }, 'image/png', 0.9);
};

const cancelCrop = () => {
  closeCropper();
};

const closeCropper = () => {
  showCropper.value = false;
  fileInput.value.value = '';

  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }

  if (tempImageUrl.value) {
    URL.revokeObjectURL(tempImageUrl.value);
    tempImageUrl.value = '';
  }
};

const handleDialogClose = () => {
  // Dialog closed without action
  closeCropper();
};

const handleSubmit = async () => {
  if (loading.value) return;

  loading.value = true;
  errors.value = {};

  try {
    // Prepare data including base64 avatar if available
    const profileData = {...formData.value};

    // Add base64 avatar if there's a new one
    if (avatarFile.value) {
      const reader = new FileReader();
      const base64Promise = new Promise((resolve) => {
        reader.onloadend = () => {
          const base64String = reader.result.split(',')[1]; // Remove data:image prefix
          resolve(base64String);
        };
        reader.readAsDataURL(avatarFile.value);
      });

      profileData.user_profile_img_base64 = await base64Promise;
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

// Cleanup
onUnmounted(() => {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
  }
  if (tempImageUrl.value) {
    URL.revokeObjectURL(tempImageUrl.value);
  }
  if (cropper.value) {
    cropper.value.destroy();
  }
});

// Watch for dialog open state changes
watch(showCropper, (newVal) => {
  if (!newVal) {
    closeCropper();
  }
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

/* Section Title styling */
.section-title {
  color: var(--md-sys-color-on-surface);
}

/* Avatar Section */
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
  flex: 1;
  color: var(--md-sys-color-on-surface-variant);
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