<template>
  <div class="page-container">
    <div class="page-card">
      <div class="page-header">
        <p class="md-typescale-body-large subtitle">Fill in the following information to create an account</p>
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
          <p class="avatar-hint md-typescale-body-small">Click to upload photo</p>
          <p v-if="errors.user_profile_img" class="error-text">{{ errors.user_profile_img[0] }}</p>
        </div>

        <!-- Form Fields Grid -->
        <div class="form-fields">
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
            label="Full Name" 
            v-model="formData.name" 
            :error="!!errors.name" 
            :error-text="errors.name" 
            @input="clearError('name')"
            @blur="validateField('name')"
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
            @blur="validateField('information_id')"
            @keyup.enter="!loading && handleSubmit()"
          >
            <md-icon slot="leading-icon">fingerprint</md-icon>
          </md-outlined-text-field>

          <md-outlined-text-field 
            :type="showPassword1 ? 'text' : 'password'" 
            label="Password" 
            v-model="formData.password1" 
            :error="!!errors.password1" 
            :error-text="errors.password1" 
            @input="clearError('password1')"
            @blur="validateField('password1')"
            @keyup.enter="!loading && handleSubmit()"
          >
            <md-icon slot="leading-icon">lock</md-icon>
            <md-icon-button slot="trailing-icon" type="button" @click="showPassword1 = !showPassword1">
              <md-icon>{{ showPassword1 ? 'visibility_off' : 'visibility' }}</md-icon>
            </md-icon-button>
          </md-outlined-text-field>

          <md-outlined-text-field 
            :type="showPassword2 ? 'text' : 'password'" 
            label="Confirm Password" 
            v-model="formData.password2" 
            :error="!!errors.password2" 
            :error-text="errors.password2" 
            @input="clearError('password2')"
            @blur="validateField('password2')"
            @keyup.enter="!loading && handleSubmit()"
          >
            <md-icon slot="leading-icon">lock</md-icon>
            <md-icon-button slot="trailing-icon" type="button" @click="showPassword2 = !showPassword2">
              <md-icon>{{ showPassword2 ? 'visibility_off' : 'visibility' }}</md-icon>
            </md-icon-button>
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
          {{ loading ? 'Creating Account...' : 'Create Account' }}
        </md-filled-button>
      </form>

      <!-- Login Link -->
      <div class="nav-section">
        <md-divider></md-divider>
        <p class="md-typescale-body-medium nav-text">
          Already have an account?
          <router-link to="/login" class="nav-link">Sign in</router-link>
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
import { register } from '@/api/auth';
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
  username: '',
  name: '',
  information_id: '',
  password1: '',
  password2: '',
  user_profile_img_base64: ''  // Add this field
});
const avatarFile = ref(null);
const avatarPreviewUrl = ref('');
const errors = ref({});
const cropper = ref(null);
const showPassword1 = ref(false);
const showPassword2 = ref(false);
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

// Validate specific field
const validateField = (field) => {
  clearError(field);
  
  switch (field) {
    case 'username':
      if (!formData.value.username.trim()) {
        errors.value.username = 'Username is required';
      } else if (formData.value.username.length < 3) {
        errors.value.username = 'Username must be at least 3 characters';
      }
      break;
      
    case 'name':
      if (!formData.value.name.trim()) {
        errors.value.name = 'Name is required';
      }
      break;
      
    case 'information_id':
      if (!formData.value.information_id.trim()) {
        errors.value.information_id = 'Information ID is required';
      }
      break;
      
    case 'password1':
      if (!formData.value.password1) {
        errors.value.password1 = 'Password is required';
      } else if (formData.value.password1.length < 6) {
        errors.value.password1 = 'Password must be at least 6 characters';
      }
      break;
      
    case 'password2':
      if (!formData.value.password2) {
        errors.value.password2 = 'Please confirm your password';
      } else if (formData.value.password1 && formData.value.password2 !== formData.value.password1) {
        errors.value.password2 = 'Passwords do not match';
      }
      break;
  }
};

// Validate all fields
const validateForm = () => {
  let isValid = true;
  
  // Clear previous errors
  Object.keys(errors.value).forEach(key => delete errors.value[key]);
  
  // Validate each field
  ['username', 'name', 'information_id', 'password1', 'password2'].forEach(field => {
    validateField(field);
    if (errors.value[field]) {
      isValid = false;
    }
  });
  
  return isValid;
};

const handleFileSelect = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate file type
  if (!/^image\/(jpe?g|png)$/i.test(file.type)) {
    errors.value.user_profile_img = ['Please select a JPG or PNG image'];
    fileInput.value.value = '';
    return;
  }

  // Validate file size
  if (file.size > 5 * 1024 * 1024) {
    errors.value.user_profile_img = ['Image size must be less than 5MB'];
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
      
      // Convert blob to Base64 for backend
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result.split(',')[1]; // Remove data:image/png;base64, prefix
        formData.value.user_profile_img_base64 = base64String;
      };
      reader.readAsDataURL(blob);
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
  
  // Validate form
  if (!validateForm()) {
    return;
  }
  
  loading.value = true;
  errors.value = {};
  
  try {
    // Register user
    const response = await register(formData.value);
    
    if (!response.success) {
      // Handle API errors
      if (response.errors) {
        // Convert array errors to string format like login page
        Object.keys(response.errors).forEach(key => {
          if (Array.isArray(response.errors[key])) {
            errors.value[key] = response.errors[key][0];
          } else {
            errors.value[key] = response.errors[key];
          }
        });
      } else {
        errors.value.general = response.detail || response.message || 'Registration failed. Please check your information.';
      }
      return;
    }
    
    // Success - avatar was already included in registration data as base64
    router.push('/');
    
  } catch (error) {
    console.error('Registration error:', error);
    errors.value.general = 'Network error. Please check your connection and try again.';
  } finally {
    loading.value = false;
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
</script>

<style scoped>
/* Page-specific styles for Register.vue */
/* All common styles are now in @/styles/auth-shared.css */
</style>