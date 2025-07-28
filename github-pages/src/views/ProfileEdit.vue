<template>
  <div class="page-container">
    <div class="page-card">
      <div class="page-header">
        <p class="md-typescale-body-large subtitle">Update your information</p>
      </div>

      <form @submit.prevent="handleSubmit" novalidate>
        <!-- Avatar Section - Centered -->
        <div class="avatar-upload-section">
          <div class="avatar-wrapper">
            <img :src="getAvatarSrc()" class="avatar-preview" alt="Avatar">
            <div class="avatar-overlay" @click="selectImage">
              <md-icon>photo_camera</md-icon>
            </div>
          </div>
          <input 
            ref="fileInput" 
            type="file" 
            class="hidden-input" 
            accept="image/jpeg,image/jpg,image/png" 
            @change="handleFileSelect"
          >
          <p class="avatar-hint md-typescale-body-small">Click to upload new photo</p>
          <p v-if="errors.user_profile_img" class="error-text">{{ errors.user_profile_img }}</p>
        </div>

        <!-- Form Fields -->
        <div class="form-fields">
          <md-outlined-text-field 
            label="Full Name" 
            v-model="formData.name" 
            :error="!!errors.name" 
            :error-text="errors.name" 
            @input="clearError('name')"
            @keyup.enter="!loading && handleSubmit()"
          >
            <md-icon slot="leading-icon">badge</md-icon>
          </md-outlined-text-field>

          <md-outlined-text-field 
            label="Information ID" 
            v-model="formData.information_id" 
            :error="!!errors.information_id" 
            :error-text="errors.information_id" 
            @input="clearError('information_id')"
            @keyup.enter="!loading && handleSubmit()"
          >
            <md-icon slot="leading-icon">fingerprint</md-icon>
          </md-outlined-text-field>
        </div>

        <!-- Error Message -->
        <div v-if="errors.general" class="error-banner">
          <md-icon>error_outline</md-icon>
          <span class="md-typescale-body-medium">{{ errors.general }}</span>
        </div>

        <!-- Submit Button -->
        <md-filled-button type="submit" :disabled="loading" class="primary-button">
          <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </md-filled-button>
      </form>

      <!-- Back Link -->
      <div class="nav-section">
        <md-divider></md-divider>
        <p class="md-typescale-body-medium nav-text">
          <router-link to="/" class="nav-link">
            <md-icon>arrow_back</md-icon>
            Back to Dashboard
          </router-link>
        </p>
      </div>
    </div>
  </div>

  <!-- Cropper Dialog -->
  <md-dialog ref="cropperDialog" :open="showCropper" @close="handleDialogClose" class="cropper-dialog">
    <div slot="headline">
      <md-icon>crop</md-icon>
      Crop Your Photo
    </div>
    <form slot="content" method="dialog" class="cropper-content">
      <div class="cropper-container" ref="cropperContainer">
        <img ref="cropperImage" class="cropper-image" alt="Image to crop">
      </div>
      <div class="cropper-tips md-typescale-body-small">
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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import { getUserProfile, updateUserProfile } from '@/api/auth';
import { baseURL } from '@/config';
import Cropper from 'cropperjs';
import 'cropperjs/dist/cropper.css';
import '@/styles/auth-shared.css';

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
      avatarFile.value = new File([blob], 'avatar.png', { type: 'image/png' });
      
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
    const profileData = { ...formData.value };
    
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
    
    // Success - redirect to dashboard
    router.push('/');
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
      formData.value = { ...response.data };
      
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
/* Page-specific styles for ProfileEdit.vue */
/* All common styles are now in @/styles/auth-shared.css */
</style> 