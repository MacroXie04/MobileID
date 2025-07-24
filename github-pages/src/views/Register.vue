<template>
  <div class="register-container">
    <div class="register-card">

      <form @submit.prevent="handleSubmit" novalidate>
        <!-- Avatar Section -->
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-camera"></i>
            Avatar
          </label>
          <div class="avatar-upload-container">
            <!-- Avatar Preview and Upload Button -->
            <div class="avatar-main">
              <img 
                ref="avatarPreview" 
                class="avatar-preview"
                :src="getAvatarSrc()" 
                alt="avatar preview"
              >
              <div class="avatar-actions">
                <input 
                  ref="fileInput" 
                  type="file" 
                  class="d-none" 
                  accept="image/jpeg,image/jpg,image/png"
                  @change="handleFileSelect"
                >
                <button type="button" class="btn btn-outline-primary btn-sm" ref="selectImageBtn" @click="selectImage">
                  <i class="fas fa-camera"></i> Select Photo
                </button>
                <button type="button" class="btn btn-outline-danger btn-sm" ref="removeImageBtn" v-if="avatarFile" @click="removeImage">
                  <i class="fas fa-times"></i> Remove
                </button>
                <small class="form-hint d-block mt-2">JPEG/PNG • Max 5 MB • Optional</small>
              </div>
            </div>
          </div>
          <div v-if="errors.user_profile_img" class="invalid-feedback">
            {{ errors.user_profile_img[0] }}
          </div>
        </div>

        <!-- Username -->
        <div class="form-group">
          <label for="username" class="form-label">
            <i class="fas fa-user"></i>
            Username
          </label>
          <input 
            id="username"
            v-model="formData.username"
            type="text" 
            class="form-control"
            :class="{ 'is-invalid': errors.username }"
            placeholder="Choose a username"
            required
          >
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username[0] }}
          </div>
        </div>

        <!-- Name -->
        <div class="form-group">
          <label for="name" class="form-label">
            <i class="fas fa-id-card"></i>
            Name
          </label>
          <input 
            id="name"
            v-model="formData.name"
            type="text" 
            class="form-control"
            :class="{ 'is-invalid': errors.name }"
            placeholder="Enter your full name"
            required
          >
          <div v-if="errors.name" class="invalid-feedback">
            {{ errors.name[0] }}
          </div>
        </div>

        <!-- Information ID -->
        <div class="form-group">
          <label for="information_id" class="form-label">
            <i class="fas fa-fingerprint"></i>
            Information ID
          </label>
          <input 
            id="information_id"
            v-model="formData.information_id"
            type="text" 
            class="form-control"
            :class="{ 'is-invalid': errors.information_id }"
            placeholder="Enter your information ID"
            required
          >
          <div v-if="errors.information_id" class="invalid-feedback">
            {{ errors.information_id[0] }}
          </div>
        </div>

        <!-- Password -->
        <div class="form-group">
          <label for="password1" class="form-label">
            <i class="fas fa-lock"></i>
            Password
          </label>
          <div class="password-input-wrapper">
            <input 
              id="password1"
              v-model="formData.password1"
              :type="showPassword1 ? 'text' : 'password'"
              class="form-control"
              :class="{ 'is-invalid': errors.password1 }"
              placeholder="Create a strong password"
              required
            >
            <button
              type="button"
              class="password-toggle"
              @click="showPassword1 = !showPassword1"
            >
              <i :class="showPassword1 ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <div v-if="errors.password1" class="invalid-feedback">
            {{ errors.password1[0] }}
          </div>
        </div>

        <!-- Confirm Password -->
        <div class="form-group">
          <label for="password2" class="form-label">
            <i class="fas fa-lock"></i>
            Confirm Password
          </label>
          <div class="password-input-wrapper">
            <input 
              id="password2"
              v-model="formData.password2"
              :type="showPassword2 ? 'text' : 'password'"
              class="form-control"
              :class="{ 'is-invalid': errors.password2 }"
              placeholder="Confirm your password"
              required
            >
            <button
              type="button"
              class="password-toggle"
              @click="showPassword2 = !showPassword2"
            >
              <i :class="showPassword2 ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <div v-if="errors.password2" class="invalid-feedback">
            {{ errors.password2[0] }}
          </div>
        </div>

        <!-- General Error Message -->
        <div v-if="errors.general" class="alert alert-danger">
          <i class="fas fa-exclamation-triangle"></i>
          {{ errors.general[0] }}
        </div>

        <!-- Submit Button -->
        <button type="submit" class="btn btn-register" :disabled="loading">
          <span v-if="!loading">
            <i class="fas fa-user-plus"></i> 
            Create Account
          </span>
          <span v-else>
            <i class="fas fa-spinner fa-spin"></i>
            Creating account...
          </span>
        </button>
      </form>

      <!-- Divider -->
      <div class="divider">
        <span>OR</span>
      </div>

      <!-- Login Link -->
      <div class="login-link">
        <p>
          Already have an account? 
          <router-link to="/login">Sign in here</router-link>
        </p>
      </div>
    </div>
  </div>

  <!-- Cropper Modal (outside main container) -->
  <Teleport to="body">
    <div class="cropper-modal" v-show="showCropper" @click.self="cancelCrop">
      <div class="cropper-content">
        <div class="cropper-header">
          <h5 class="cropper-title">Crop Your Photo</h5>
          <button type="button" class="btn-close" @click="cancelCrop">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="crop-area" ref="cropArea">
          <img ref="cropperImage" alt="">
        </div>
        <div class="cropper-footer">
          <small class="crop-hint">Drag to move • Scroll to zoom</small>
          <div class="control-buttons">
            <button type="button" class="btn btn-outline" @click="resetCrop">
              <i class="fas fa-undo"></i> Reset
            </button>
            <button type="button" class="btn btn-primary" ref="applyCropBtn" @click="applyCrop">
              <i class="fas fa-check"></i> Apply Crop
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
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
</script>

<style scoped>
@import 'cropperjs/dist/cropper.css';

.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  transition: transform 0.3s ease;
}

/* Header Section */
.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-container {
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 60px;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.register-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 10px;
}

.register-subtitle {
  color: #666;
  font-size: 16px;
}

/* Form Styling */
.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.form-label i {
  margin-right: 8px;
  color: #667eea;
}

.form-control {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-control.is-invalid {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.form-control.is-invalid:focus {
  box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.1);
}

/* Password Input Wrapper */
.password-input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 8px;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: #333;
}

.password-input-wrapper .form-control {
  padding-right: 48px;
}

/* Error Messages */
.invalid-feedback {
  display: block;
  margin-top: 6px;
  color: #dc3545;
  font-size: 14px;
  font-weight: 500;
}

.alert {
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.alert-danger {
  background-color: #fee;
  color: #c53030;
  border: 1px solid #feb2b2;
}

/* Avatar Upload Section */
.avatar-upload-container {
  position: relative;
}

.avatar-main {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 50%;
  border: 3px solid #e0e0e0;
  background: #f8f9fa;
  flex-shrink: 0;
}

.avatar-actions {
  flex: 1;
}

.avatar-actions .btn {
  margin-right: 8px;
  margin-bottom: 8px;
}

.form-hint {
  color: #666;
  font-size: 12px;
  margin: 0;
}

/* Cropper Modal */
.cropper-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.cropper-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.cropper-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
}

.cropper-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  color: #666;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #e0e0e0;
  color: #333;
}

.crop-area {
  height: 400px;
  background: #f0f0f0;
  position: relative;
  overflow: hidden;
  flex: 1;
}

.crop-area img {
  display: block;
  max-width: 100%;
}

.cropper-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
}

.crop-hint {
  color: #666;
  font-size: 12px;
}

.control-buttons {
  display: flex;
  gap: 8px;
}

/* Buttons */
.btn {
  border: none;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-register {
  width: 100%;
  padding: 14px 24px;
  font-size: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.btn-register:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-register:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-outline {
  background: white;
  border: 2px solid #e0e0e0;
  color: #666;
}

.btn-outline:hover {
  border-color: #999;
  color: #333;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a67d8;
}

.btn-outline-primary {
  background: white;
  border: 2px solid #667eea;
  color: #667eea;
}

.btn-outline-primary:hover {
  background: #667eea;
  color: white;
}

.btn-outline-danger {
  background: white;
  border: 2px solid #dc3545;
  color: #dc3545;
}

.btn-outline-danger:hover {
  background: #dc3545;
  color: white;
}

/* Divider */
.divider {
  text-align: center;
  margin: 30px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e0e0e0;
}

.divider span {
  background: white;
  padding: 0 16px;
  position: relative;
  color: #666;
  font-size: 14px;
}

/* Login Link */
.login-link {
  text-align: center;
  margin-top: 20px;
}

.login-link p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.login-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.login-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Hidden utility */
.d-none {
  display: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .register-card {
    padding: 30px 20px;
    max-width: 100%;
  }
  
  .avatar-main {
    flex-direction: column;
    text-align: center;
  }
  
  .form-control {
    font-size: 16px; /* Prevent zoom on iOS */
  }
  
  .cropper-footer {
    flex-direction: column;
    gap: 12px;
  }
  
  .control-buttons {
    width: 100%;
    justify-content: center;
  }
}
</style> 