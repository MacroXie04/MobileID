<template>
  <div
    class="container mt-5 d-flex justify-content-center align-items-center"
    style="min-height: 80vh;"
  >
    <div
      class="card p-4 shadow-sm"
      style="max-width: 800px; width: 100%;"
    >
      <h3 class="text-center mb-4 fw-semibold">
        Edit Profile
      </h3>

      <form
        id="profileForm"
        @submit.prevent="handleSubmit"
        novalidate
      >
        <!-- Avatar Section -->
        <div class="mb-4">
          <label class="form-label fw-semibold">
            Profile Picture
          </label>

          <div class="avatar-section">
            <!-- Preview Section -->
            <div class="preview-section text-center">
              <img
                ref="avatarPreview"
                class="avatar-preview mb-2"
                :src="getAvatarSrc()"
                alt="avatar preview"
              />
              <div class="small text-muted">
                Preview
              </div>
            </div>

            <!-- Cropper Section -->
            <div class="cropper-section">
              <div
                class="cropper-container"
                ref="cropperContainer"
              >
                <div
                  class="crop-area"
                  ref="cropArea"
                >
                  <div class="crop-placeholder" ref="cropPlaceholder">
                    <i
                      class="fas fa-cloud-upload-alt mb-2 d-block"
                      style="font-size: 2rem;"
                    ></i>
                    Click "Select Image" to upload and crop your avatar
                  </div>
                  <img
                    ref="cropperImage"
                    style="display: none;"
                    alt=""
                  />
                </div>

                <div
                  class="crop-controls"
                  ref="cropControls"
                >
                  <div class="d-flex gap-2 justify-content-between align-items-center">
                    <small class="text-muted">
                      Drag to reposition • Scroll to zoom
                    </small>
                    <div class="d-flex gap-2">
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm"
                        @click="resetCrop"
                      >
                        <i class="fas fa-undo"></i>
                        Reset
                      </button>
                      <button
                        type="button"
                        class="btn btn-primary btn-sm"
                        ref="applyCropBtn"
                        @click="applyCrop"
                      >
                        <i class="fas fa-check"></i>
                        Apply
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-2">
                <input
                  ref="fileInput"
                  type="file"
                  class="d-none"
                  accept="image/jpeg,image/jpg,image/png"
                  @change="handleFileSelect"
                />

                <button
                  ref="selectImageBtn"
                  type="button"
                  class="btn btn-outline-primary"
                  @click="selectImage"
                >
                  <i class="fas fa-image"></i>
                  Select Image
                </button>
                <button
                  ref="removeImageBtn"
                  type="button"
                  class="btn btn-outline-danger ms-2"
                  style="display: none;"
                  @click="removeImage"
                >
                  <i class="fas fa-trash"></i>
                  Remove
                </button>
              </div>

              <div v-if="errors.user_profile_img" class="invalid-feedback d-block text-start mt-1">
                {{ errors.user_profile_img }}
              </div>
              <small class="text-muted d-block mt-1">
                JPEG/PNG • Max 5 MB • Will be resized to 128×128px
              </small>
            </div>
          </div>
        </div>

        <!-- Name Field -->
        <div class="mb-3">
          <label for="name" class="form-label">Name</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.name }"
            required
          />
          <div v-if="errors.name" class="invalid-feedback">
            {{ errors.name }}
          </div>
        </div>

        <!-- Information ID Field -->
        <div class="mb-3">
          <label for="information_id" class="form-label">Information ID</label>
          <input
            id="information_id"
            v-model="formData.information_id"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.information_id }"
            required
          />
          <div v-if="errors.information_id" class="invalid-feedback">
            {{ errors.information_id }}
          </div>
        </div>

        <div v-if="errors.general" class="invalid-feedback d-block mb-3">
          {{ errors.general }}
        </div>

        <button
          class="btn btn-primary w-100 py-2"
          type="submit"
          :disabled="loading"
        >
          <i class="fas fa-save"></i>
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { getUserProfile, updateUserProfile } from '@/api/auth';
import Cropper from 'cropperjs';

const router = useRouter();

// Refs
const avatarPreview = ref(null);
const fileInput = ref(null);
const selectImageBtn = ref(null);
const removeImageBtn = ref(null);
const cropperImage = ref(null);
const cropArea = ref(null);
const cropControls = ref(null);
const cropperContainer = ref(null);
const applyCropBtn = ref(null);
const cropPlaceholder = ref(null);

// State
const loading = ref(false);
const formData = ref({
  name: '',
  information_id: '',
  user_profile_img: ''
});
const errors = ref({});
const cropper = ref(null);
const originalImageSrc = ref(null);

// Methods
const getAvatarSrc = () => {
  if (formData.value.user_profile_img) {
    return `data:image/png;base64,${formData.value.user_profile_img}`;
  }
  return '/images/avatar_placeholder.png';
};

const updateButtons = (editing) => {
  if (editing) {
    selectImageBtn.value.style.display = 'none';
    cropControls.value.classList.add('show');
  } else {
    selectImageBtn.value.style.display = 'inline-block';
    cropControls.value.classList.remove('show');
  }
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
  cropperImage.value.src = originalImageSrc.value;
  cropperImage.value.style.display = 'block';
  cropPlaceholder.value.style.display = 'none';
  cropperContainer.value.classList.add('active');
  removeImageBtn.value.style.display = 'inline-block';
  updateButtons(true);

  nextTick(() => {
    cropper.value = new Cropper(cropperImage.value, {
      aspectRatio: 1,
      viewMode: 1,
      autoCropArea: 0.8,
      responsive: true,
      restore: false,
      checkOrientation: false,
      modal: false,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: true,
      cropBoxResizable: true,
      toggleDragModeOnDblclick: false,
    });
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
  
  const dataURL = canvas.toDataURL('image/png', 0.9);
  formData.value.user_profile_img = dataURL.split(',')[1];
  avatarPreview.value.src = dataURL;
  fileInput.value.value = '';

  applyCropBtn.value.innerHTML = '<i class="fas fa-check"></i> Applied!';
  applyCropBtn.value.classList.replace('btn-primary', 'btn-success');

  setTimeout(() => {
    applyCropBtn.value.innerHTML = '<i class="fas fa-check"></i> Apply';
    applyCropBtn.value.classList.replace('btn-success', 'btn-primary');
  }, 1000);

  cropperContainer.value.classList.remove('active');
  updateButtons(false);
};

const removeImage = () => {
  formData.value.user_profile_img = '';
  fileInput.value.value = '';
  avatarPreview.value.src = '/images/avatar_placeholder.png';

  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = null;
  }
  cropperImage.value.style.display = 'none';
  cropPlaceholder.value.style.display = 'block';
  cropperContainer.value.classList.remove('active');
  updateButtons(false);
  removeImageBtn.value.style.display = 'none';

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
    const response = await updateUserProfile(formData.value);
    if (response.success) {
      alert('Profile updated successfully!');
      router.push('/');
    } else {
      if (response.errors) {
        errors.value = response.errors;
      } else {
        errors.value.general = response.message || 'Update failed';
      }
    }
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
      
      // Update UI state
      const hasImage = Boolean(formData.value.user_profile_img);
      if (hasImage) {
        removeImageBtn.value.style.display = 'inline-block';
      } else {
        removeImageBtn.value.style.display = 'none';
      }
      updateButtons(false);
    }
  } catch (error) {
    console.error('Failed to load profile:', error);
    errors.value.general = 'Failed to load profile data';
  }
};

// Lifecycle
onMounted(() => {
  loadProfile();
});

onUnmounted(() => {
  if (originalImageSrc.value) {
    URL.revokeObjectURL(originalImageSrc.value);
  }
  if (cropper.value) {
    cropper.value.destroy();
  }
});
</script>

<style scoped>
.avatar-preview {
  width: 128px;
  height: 128px;
  object-fit: cover;
  border-radius: .25rem;
  border: 1px solid #dee2e6;
}

.cropper-container {
  border: 2px dashed #dee2e6;
  border-radius: .5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
}

.cropper-container.active {
  border-color: #0d6efd;
  background-color: #fff;
}

.crop-area {
  height: 300px;
  width: 100%;
  border-radius: .25rem;
  overflow: hidden;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.crop-placeholder {
  color: #6c757d;
  font-size: 0.9rem;
}

.crop-controls {
  margin-top: 1rem;
  display: none;
}

.crop-controls.show {
  display: block;
}

.avatar-section {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.preview-section {
  flex-shrink: 0;
}

.cropper-section {
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .avatar-section {
    flex-direction: column;
    gap: 1rem;
  }

  .preview-section {
    align-self: center;
  }
}
</style> 