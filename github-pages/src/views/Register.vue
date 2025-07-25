<template>
  <div class="register-container">
    <div class="register-card">
      <form @submit.prevent="handleSubmit" novalidate>
        <!-- Avatar Section -->
        <div class="avatar-section">
          <img :src="getAvatarSrc()" class="avatar-preview" alt="Avatar">
          <input ref="fileInput" type="file" class="d-none" accept="image/*" @change="handleFileSelect">
          <md-filled-tonal-button @click="selectImage">Select Photo</md-filled-tonal-button>
          <p v-if="errors.user_profile_img" class="error-text">{{ errors.user_profile_img[0] }}</p>
        </div>

        <md-outlined-text-field label="Username" v-model="formData.username" :error="!!errors.username" :error-text="errors.username ? errors.username[0] : ''" @keyup.enter="!loading && handleSubmit()">
          <md-icon slot="leading-icon">person</md-icon>
        </md-outlined-text-field>

        <md-outlined-text-field label="Name" v-model="formData.name" :error="!!errors.name" :error-text="errors.name ? errors.name[0] : ''" @keyup.enter="!loading && handleSubmit()">
          <md-icon slot="leading-icon">badge</md-icon>
        </md-outlined-text-field>

        <md-outlined-text-field label="Information ID" v-model="formData.information_id" :error="!!errors.information_id" :error-text="errors.information_id ? errors.information_id[0] : ''" @keyup.enter="!loading && handleSubmit()">
          <md-icon slot="leading-icon">fingerprint</md-icon>
        </md-outlined-text-field>

        <md-outlined-text-field :type="showPassword1 ? 'text' : 'password'" label="Password" v-model="formData.password1" :error="!!errors.password1" :error-text="errors.password1 ? errors.password1[0] : ''" @keyup.enter="!loading && handleSubmit()">
          <md-icon slot="leading-icon">lock</md-icon>
          <md-icon-button slot="trailing-icon" type="button" @click="showPassword1 = !showPassword1">
            <md-icon>{{ showPassword1 ? 'visibility_off' : 'visibility' }}</md-icon>
          </md-icon-button>
        </md-outlined-text-field>

        <md-outlined-text-field :type="showPassword2 ? 'text' : 'password'" label="Confirm Password" v-model="formData.password2" :error="!!errors.password2" :error-text="errors.password2 ? errors.password2[0] : ''" @keyup.enter="!loading && handleSubmit()">
          <md-icon slot="leading-icon">lock</md-icon>
          <md-icon-button slot="trailing-icon" type="button" @click="showPassword2 = !showPassword2">
            <md-icon>{{ showPassword2 ? 'visibility_off' : 'visibility' }}</md-icon>
          </md-icon-button>
        </md-outlined-text-field>

        <div v-if="errors.general" class="error-banner">
          <md-icon>error_outline</md-icon>
          <span class="md-typescale-body-medium">{{ Array.isArray(errors.general) ? errors.general[0] : errors.general }}</span>
        </div>

        <md-filled-button type="submit" :disabled="loading">{{ loading ? 'Creating...' : 'Create Account' }}</md-filled-button>
      </form>

      <md-divider class="divider"></md-divider>

      <div class="login-link md-typescale-body-medium">
        Already have an account?
        <router-link to="/login">
          <md-text-button><md-icon slot="icon">login</md-icon>Sign in</md-text-button>
        </router-link>
      </div>
    </div>
  </div>

  <!-- Cropper Dialog -->
  <md-dialog :open="showCropper" @closed="handleDialogClose">
    <div slot="headline">Crop Your Photo</div>
    <div slot="content">
      <div ref="cropArea">
        <img ref="cropperImage" alt="">
      </div>
    </div>
    <div slot="actions">
      <md-text-button value="reset" @click="resetCrop">Reset</md-text-button>
      <md-text-button value="cancel" @click="cancelCrop">Cancel</md-text-button>
      <md-filled-button value="apply" @click="applyCrop">Apply</md-filled-button>
    </div>
  </md-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { register, uploadAvatar } from '@/api/auth';
import Cropper from 'cropperjs';

const router = useRouter();

// Refs
const avatarPreview = ref(null);
const fileInput = ref(null);
const selectImageBtn = ref(null);
const removeImageBtn = ref(null);
const cropperImage = ref(null);
const cropArea = ref(null);
const cropperModal = ref(null);
const applyCropBtn = ref(null);

// State
const loading = ref(false);
const formData = ref({
  username: '',
  name: '',
  information_id: '',
  password1: '',
  password2: ''
});
const avatarFile = ref(null); // Store the file to upload after registration
const avatarPreviewUrl = ref(''); // Store preview URL
const errors = ref({});
const cropper = ref(null);
const originalImageSrc = ref(null);
const showPassword1 = ref(false);
const showPassword2 = ref(false);
const showCropper = ref(false);

// Methods
const getAvatarSrc = () => {
  if (avatarPreviewUrl.value) {
    return avatarPreviewUrl.value;
  }
  return '/images/avatar_placeholder.png';
};

const selectImage = () => {
  fileInput.value.click();
};

const handleFileSelect = (e) => {
  if (!e.target.files.length) return;
  const file = e.target.files[0];

  if (!/^image\/(jpe?g|png)$/i.test(file.type)) {
    alert('Only JPG and PNG images are supported.');
    fileInput.value.value = '';
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('File size must be less than 5MB.');
    fileInput.value.value = '';
    return;
  }
  console.log('Loading image to cropper...');
  loadImageToCropper(file);
};

const loadImageToCropper = (file) => {
  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }
  
  if (originalImageSrc.value) {
    URL.revokeObjectURL(originalImageSrc.value);
  }
  
  originalImageSrc.value = URL.createObjectURL(file);
  
  // Set showCropper to true first
  showCropper.value = true;
  console.log('showCropper set to:', showCropper.value);
  
  // Wait for DOM update before initializing cropper
  nextTick(() => {
    if (!cropperImage.value) {
      console.error('Cropper image element not found');
      return;
    }
    
    cropperImage.value.src = originalImageSrc.value;
    
    // Initialize cropper after image loads
    cropperImage.value.onload = () => {
      console.log('Image loaded, initializing cropper...');
      cropper.value = new Cropper(cropperImage.value, {
        aspectRatio: 1,
        viewMode: 1,
        autoCropArea: 0.8,
        responsive: true,
        restore: false,
        checkOrientation: false,
        modal: true,
        guides: true,
        center: true,
        highlight: false,
        background: true,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
      });
    };
  });
};

const resetCrop = () => {
  if (cropper.value) cropper.value.reset();
};

const applyCrop = () => {
  if (!cropper.value) return;
  
  const canvas = cropper.value.getCroppedCanvas({
    width: 128,
    height: 128,
    imageSmoothingQuality: 'high'
  });
  
  // Convert cropped canvas to blob
  canvas.toBlob((blob) => {
    if (blob) {
      // Store the file for upload after registration
      avatarFile.value = new File([blob], 'avatar.png', { type: 'image/png' });
      
      // Create preview URL
      if (avatarPreviewUrl.value) {
        URL.revokeObjectURL(avatarPreviewUrl.value);
      }
      avatarPreviewUrl.value = URL.createObjectURL(blob);
      avatarPreview.value.src = avatarPreviewUrl.value;
    }
  }, 'image/png', 0.9);
  
  fileInput.value.value = '';
  showCropper.value = false;
  
  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }
};

const cancelCrop = () => {
  showCropper.value = false;
  fileInput.value.value = '';
  
  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }
  
  if (originalImageSrc.value) {
    URL.revokeObjectURL(originalImageSrc.value);
    originalImageSrc.value = null;
  }
};

const removeImage = () => {
  avatarFile.value = null;
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
    avatarPreviewUrl.value = '';
  }
  fileInput.value.value = '';
  avatarPreview.value.src = '/images/avatar_placeholder.png';

  if (originalImageSrc.value) {
    URL.revokeObjectURL(originalImageSrc.value);
    originalImageSrc.value = null;
  }
};

const handleSubmit = async () => {
  if (loading.value) return;
  
  loading.value = true;
  errors.value = {};
  
  try {
    // First register the user without avatar
    const response = await register(formData.value);
    if (!response.success) {
      if (response.errors) {
        errors.value = response.errors;
      } else {
        errors.value.general = [response.message || 'Registration failed'];
      }
      return;
    }
    
    // If registration successful and there's an avatar to upload
    if (avatarFile.value) {
      try {
        await uploadAvatar(avatarFile.value);
      } catch (avatarError) {
        console.error('Avatar upload error:', avatarError);
        // Registration successful but avatar failed - still redirect
        alert('Registration successful! Avatar upload failed, you can upload it later from your profile.');
        router.push('/');
        return;
      }
    }
    
    alert('Registration successful! Welcome!');
    router.push('/');
  } catch (error) {
    console.error('Registration error:', error);
    
    // if error is not JSON, try to parse it
    try {
      const errorData = JSON.parse(error.message);
      if (errorData.errors) {
        errors.value = errorData.errors;
      } else if (errorData.message) {
        errors.value.general = [errorData.message];
      } else if (errorData.detail) {
        errors.value.general = [errorData.detail];
      } else {
        errors.value.general = ['Registration failed. Please try again.'];
      }
    } catch (parseError) {
      // if cannot parse error info, use default error
      errors.value.general = ['Network error. Please try again.'];
    }
  } finally {
    loading.value = false;
  }
};

// Lifecycle
onMounted(() => {
  // Initial state - cropper should be hidden
  showCropper.value = false;
});

onUnmounted(() => {
  if (originalImageSrc.value) {
    URL.revokeObjectURL(originalImageSrc.value);
  }
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
  }
  if (cropper.value) {
    cropper.value.destroy();
  }
});

// Add method for dialog close
const handleDialogClose = (event) => {
  if (event.detail.action === 'apply') {
    applyCrop();
  } else if (event.detail.action === 'reset') {
    resetCrop();
    // Do not close on reset
    return;
  } else {
    cancelCrop();
  }
  showCropper.value = false;
};
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background-color: var(--md-sys-color-background);
}

.register-card {
  width: 100%;
  max-width: 500px;
  padding: 24px;
  border-radius: 28px;
  background-color: var(--md-sys-color-surface);
  border: 2px solid #D1D5DB;
  box-shadow: none;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.divider {
  margin: 16px 0;
}

.login-link {
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 16px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #fff;
  color: #d32f2f;
  border-radius: 12px;
  margin: 12px 0;
  border: 2px solid #d32f2f;
  font-weight: 500;
}

.error-text {
  color: #d32f2f;
  font-size: 0.95em;
  margin-top: 4px;
}

.d-none {
  display: none !important;
}
</style> 