<template>
  <div class="page-container">
    <div class="page-card">
      <div class="page-header">
        <p class="md-typescale-body-large subtitle">Update your information</p>
      </div>

      <form novalidate @submit.prevent="handleSubmit">
        <!-- Avatar Section - Centered -->
        <div class="avatar-upload-section">
          <div class="avatar-wrapper">
            <img :src="getAvatarSrc()" alt="Avatar" class="avatar-preview">
            <div class="avatar-overlay" @click="selectImage">
              <md-icon>photo_camera</md-icon>
            </div>
          </div>
          <input
              ref="fileInput"
              accept="image/jpeg,image/jpg,image/png"
              class="hidden-input"
              type="file"
              @change="handleFileSelect"
          >
          <p class="avatar-hint md-typescale-body-small">Click to upload new photo</p>
          <p v-if="errors.user_profile_img" class="error-text">{{ errors.user_profile_img }}</p>
        </div>

        <!-- Form Fields -->
        <div class="form-fields">
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

        <!-- Error Message -->
        <div v-if="errors.general" class="error-banner">
          <md-icon>error_outline</md-icon>
          <span class="md-typescale-body-medium">{{ errors.general }}</span>
        </div>

        <!-- Submit Button -->
        <md-filled-button :disabled="loading" class="primary-button" type="submit">
          <md-circular-progress v-if="loading" indeterminate></md-circular-progress>
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </md-filled-button>
      </form>

      <!-- Passkey Management Section -->
      <div v-if="webAuthnSupported" class="passkey-section">
        <md-divider></md-divider>

        <div class="section-header">
          <h3 class="md-typescale-title-medium">Passkeys</h3>
          <p class="md-typescale-body-small section-description">
            Passkeys provide a secure and convenient way to sign in without passwords
          </p>
        </div>

        <!-- Passkeys List -->
        <div v-if="passkeys.length > 0" class="passkeys-list">
          <div v-for="passkey in passkeys" :key="passkey.id" class="passkey-item">
            <div class="passkey-info">
              <md-icon>key</md-icon>
              <div class="passkey-details">
                <p class="md-typescale-body-medium">Passkey</p>
                <p class="md-typescale-body-small passkey-date">
                  Added {{ formatDate(passkey.created_at) }}
                </p>
              </div>
            </div>
            <md-icon-button @click="confirmDeletePasskey(passkey.id)">
              <md-icon>delete</md-icon>
            </md-icon-button>
          </div>
        </div>

        <!-- Add Passkey Button -->
        <md-outlined-button
            :disabled="passkeyLoading"
            class="add-passkey-button"
            @click="handleAddPasskey"
        >
          <md-icon slot="icon">add</md-icon>
          {{ passkeyLoading ? 'Setting up...' : 'Add a Passkey' }}
        </md-outlined-button>

        <!-- Success/Error Messages for Passkey Operations -->
        <div v-if="passkeyMessage" :class="['message-banner', passkeyMessageType]">
          <md-icon>{{ passkeyMessageType === 'success' ? 'check_circle' : 'error_outline' }}</md-icon>
          <span class="md-typescale-body-medium">{{ passkeyMessage }}</span>
        </div>
      </div>

      <!-- Back Link -->
      <div class="nav-section">
        <md-divider></md-divider>
        <p class="md-typescale-body-medium nav-text">
          <router-link class="nav-link" to="/">
            <md-icon>arrow_back</md-icon>
            Back to Dashboard
          </router-link>
        </p>
      </div>
    </div>
  </div>

  <!-- Cropper Dialog -->
  <md-dialog ref="cropperDialog" :open="showCropper" class="cropper-dialog" @close="handleDialogClose">
    <div slot="headline">
      <md-icon>crop</md-icon>
      Crop Your Photo
    </div>
    <form slot="content" class="cropper-content" method="dialog">
      <div ref="cropperContainer" class="cropper-container">
        <img ref="cropperImage" alt="Image to crop" class="cropper-image">
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

  <!-- Delete Passkey Confirmation Dialog -->
  <md-dialog ref="deleteDialog" :open="showDeleteDialog" @close="() => showDeleteDialog = false">
    <div slot="headline">Delete Passkey?</div>
    <form slot="content" method="dialog">
      <p class="md-typescale-body-medium">
        Are you sure you want to delete this passkey? You won't be able to use it to sign in anymore.
      </p>
    </form>
    <div slot="actions">
      <md-text-button @click="() => showDeleteDialog = false">Cancel</md-text-button>
      <md-filled-button @click="handleDeletePasskey">Delete</md-filled-button>
    </div>
  </md-dialog>
</template>

<script setup>
import {nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {getUserProfile, updateUserProfile} from '@/api/auth';
import {deletePasskey, getPasskeys, isWebAuthnSupported, registerPasskey} from '@/api/passkeys';
import {baseURL} from '@/config';
import Cropper from 'cropperjs';
import 'cropperjs/dist/cropper.css';
import '@/styles/auth-shared.css';

const router = useRouter();

// Refs
const fileInput = ref(null);
const cropperImage = ref(null);
const cropperContainer = ref(null);
const cropperDialog = ref(null);
const deleteDialog = ref(null);

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

// Passkey related state
const webAuthnSupported = ref(false);
const passkeys = ref([]);
const passkeyLoading = ref(false);
const passkeyMessage = ref('');
const passkeyMessageType = ref('');
const showDeleteDialog = ref(false);
const passkeyToDelete = ref(null);

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

// Passkey management functions
const loadPasskeys = async () => {
  try {
    const response = await getPasskeys();
    if (response.success) {
      passkeys.value = response.passkeys;
    }
  } catch (error) {
    console.error('Failed to load passkeys:', error);
  }
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return 'today';
  } else if (diffDays === 1) {
    return 'yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
};

const handleAddPasskey = async () => {
  passkeyLoading.value = true;
  passkeyMessage.value = '';

  try {
    const result = await registerPasskey();

    if (result.success) {
      passkeyMessage.value = 'Passkey added successfully!';
      passkeyMessageType.value = 'success';
      await loadPasskeys(); // Reload the list

      // Clear message after 3 seconds
      setTimeout(() => {
        passkeyMessage.value = '';
      }, 3000);
    } else {
      passkeyMessage.value = result.message || 'Failed to add passkey';
      passkeyMessageType.value = 'error';
    }
  } catch (error) {
    console.error('Passkey registration error:', error);

    // Handle specific errors
    if (error.name === 'NotAllowedError') {
      passkeyMessage.value = 'Registration was cancelled or not allowed';
    } else if (error.name === 'InvalidStateError') {
      passkeyMessage.value = 'A passkey already exists for this device';
    } else {
      passkeyMessage.value = 'Failed to add passkey. Please try again.';
    }
    passkeyMessageType.value = 'error';
  } finally {
    passkeyLoading.value = false;
  }
};

const confirmDeletePasskey = (passkeyId) => {
  passkeyToDelete.value = passkeyId;
  showDeleteDialog.value = true;
};

const handleDeletePasskey = async () => {
  if (!passkeyToDelete.value) return;

  try {
    const result = await deletePasskey(passkeyToDelete.value);

    if (result.success) {
      passkeyMessage.value = 'Passkey deleted successfully';
      passkeyMessageType.value = 'success';
      await loadPasskeys(); // Reload the list

      // Clear message after 3 seconds
      setTimeout(() => {
        passkeyMessage.value = '';
      }, 3000);
    } else {
      passkeyMessage.value = result.message || 'Failed to delete passkey';
      passkeyMessageType.value = 'error';
    }
  } catch (error) {
    console.error('Failed to delete passkey:', error);
    passkeyMessage.value = 'Failed to delete passkey';
    passkeyMessageType.value = 'error';
  } finally {
    showDeleteDialog.value = false;
    passkeyToDelete.value = null;
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
  // Check WebAuthn support
  webAuthnSupported.value = isWebAuthnSupported();

  loadProfile();

  // Load passkeys if WebAuthn is supported
  if (webAuthnSupported.value) {
    loadPasskeys();
  }
});
</script>

<style scoped>
/* Page-specific styles for ProfileEdit.vue */
/* All common styles are now in @/styles/auth-shared.css */

/* Passkey Section Styles */
.passkey-section {
  margin-top: 32px;
}

.section-header {
  margin: 24px 0 16px 0;
}

.section-description {
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

.passkeys-list {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.passkey-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background-color: var(--md-sys-color-surface-variant);
  border-radius: 8px;
}

.passkey-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.passkey-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.passkey-date {
  color: var(--md-sys-color-on-surface-variant);
}

.add-passkey-button {
  width: 100%;
  margin-top: 16px;
}

.message-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 4px;
  margin-top: 12px;
}

.message-banner.success {
  background-color: var(--md-sys-color-success-container);
  color: var(--md-sys-color-on-success-container);
}

.message-banner.error {
  background-color: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}
</style> 