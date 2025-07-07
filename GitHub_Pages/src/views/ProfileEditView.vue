<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Edit Profile</h3>

      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>

      <form novalidate @submit.prevent="handleUpdate">
        <div class="mb-3 text-center">
          <img v-if="avatarPreview" :src="avatarPreview" alt="Avatar Preview"
               class="avatar-preview mb-2">
          <div v-if="!imageToCrop">
            <button class="btn btn-outline-secondary w-100" type="button" @click="triggerFileInput">
              Change Avatar
            </button>
            <input ref="fileInput" accept="image/*" class="d-none" type="file"
                   @change="onFileChange">
          </div>
        </div>

        <div v-if="imageToCrop" class="mb-3">
          <vue-cropper ref="cropper" :aspect-ratio="1" :src="imageToCrop" style="height: 400px;"
                       view-mode="1"></vue-cropper>
          <div class="d-flex justify-content-center mt-2">
            <button class="btn btn-primary" type="button" @click="cropAndSetAvatar">Crop & Use
            </button>
            <button class="btn btn-link" type="button" @click="cancelCrop">Cancel</button>
          </div>
        </div>

        <div class="mb-3">
          <label for="username">Username</label>
          <input id="username" :value="form.username" class="form-control" disabled type="text">
          <small class="form-text text-muted">Username cannot be changed.</small>
        </div>

        <div class="mb-3">
          <label for="name">Full Name</label>
          <input id="name" v-model="form.name" :class="{'is-invalid': errors.name}" class="form-control"
                 type="text">
          <div v-if="errors.name" class="invalid-feedback">{{ errors.name[0] }}</div>
        </div>
        <div class="mb-3">
          <label for="student_id">Student ID</label>
          <input id="student_id" v-model="form.student_id" :class="{'is-invalid': errors.student_id}" class="form-control"
                 type="text">
          <div v-if="errors.student_id" class="invalid-feedback">{{ errors.student_id[0] }}</div>
        </div>

        <div v-if="errors.detail" class="alert alert-danger">{{ errors.detail }}</div>

        <div class="d-grid gap-2">
          <button :disabled="isSaving" class="btn btn-primary py-2" type="submit">
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
          <router-link class="btn btn-secondary" to="/">Back to Home</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import apiClient from '@/api';
import VueCropper from 'vue-cropperjs';
import {useRouter} from 'vue-router';

// --- State ---
const router = useRouter();
const form = reactive({
  username: '',
  name: '',
  student_id: '',
  user_profile_img: '',
});
const originalData = ref({});
const errors = ref({});
const successMessage = ref('');
const isSaving = ref(false);

// --- Image & Cropper ---
const avatarPreview = ref(null);
const imageToCrop = ref(null);
const fileInput = ref(null);
const cropper = ref(null);
let newAvatarData = null;

onMounted(async () => {
  try {
    const {data} = await apiClient.get('/me/');
    // Populate form with existing data
    form.username = data.username;
    form.name = data.name;
    form.student_id = data.student_id;
    originalData.value = {...data}; // Store original data
    avatarPreview.value = `data:image/png;base64,${data.user_profile_img}`;
  } catch (err) {
    console.error("Failed to load profile", err);
    errors.value = {detail: "Could not load your profile data."};
  }
});

const triggerFileInput = () => fileInput.value.click();
const onFileChange = (e) => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      imageToCrop.value = event.target.result;
    };
    reader.readAsDataURL(file);
  }
};
const cancelCrop = () => {
  imageToCrop.value = null;
};
const cropAndSetAvatar = () => {
  if (!cropper.value) return;
  const dataUrl = cropper.value.getCroppedCanvas({width: 128, height: 128}).toDataURL('image/png');
  newAvatarData = dataUrl.split(',')[1];
  avatarPreview.value = dataUrl;
  imageToCrop.value = null;
};

// --- Form Submission ---
const handleUpdate = async () => {
  isSaving.value = true;
  errors.value = {};
  successMessage.value = '';

  // Only send data that has changed (PATCH method is ideal)
  const payload = {};
  if (form.name !== originalData.value.name) {
    payload.name = form.name;
  }
  if (form.student_id !== originalData.value.student_id) {
    payload.student_id = form.student_id;
  }
  if (newAvatarData) { // Only include image if it was changed
    payload.user_profile_img = newAvatarData;
  }

  // If no data changed, just show a success message
  if (Object.keys(payload).length === 0) {
    successMessage.value = "No changes to save.";
    isSaving.value = false;
    return;
  }

  try {
    // Using PATCH to send only modified fields
    const {data} = await apiClient.patch('/me/', payload);
    successMessage.value = 'Profile updated successfully!';
    originalData.value = {...originalData.value, ...data};
    newAvatarData = null;
  } catch (err) {
    if (err.response?.status === 400) {
      errors.value = err.response.data;
    } else {
      errors.value = {detail: "An unexpected error occurred."};
    }
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.avatar-preview {
  width: 128px;
  height: 128px;
  object-fit: cover;
  background-color: #fff;
  margin: 0 auto;
}
</style>
