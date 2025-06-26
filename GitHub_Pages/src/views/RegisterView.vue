<template>
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4 fw-semibold">Create Account</h3>

      <form @submit.prevent="handleRegister" novalidate>
        <div class="mb-3 text-center">
          <img v-if="avatarPreview" :src="avatarPreview" class="avatar-preview mb-2"
               alt="Avatar Preview">

          <div v-if="!imageToCrop">
            <button type="button" @click="triggerFileInput" class="btn btn-outline-secondary w-100">
              Select Avatar
            </button>
            <input type="file" ref="fileInput" @change="onFileChange" accept="image/*"
                   class="d-none">
          </div>

          <div v-if="errors.user_profile_img" class="invalid-feedback d-block text-start">
            {{ errors.user_profile_img[0] }}
          </div>
        </div>

        <div v-if="imageToCrop" class="mb-3">
          <vue-cropper
            ref="cropper"
            :src="imageToCrop"
            :aspect-ratio="1"
            view-mode="1"
            style="height: 400px;"
          ></vue-cropper>
          <div class="d-flex justify-content-center mt-2">
            <button type="button" class="btn btn-primary" @click="cropAndSetAvatar">Crop & Use
            </button>
            <button type="button" class="btn btn-link" @click="cancelCrop">Cancel</button>
          </div>
        </div>

        <div class="mb-3">
          <label for="username">Username</label>
          <input type="text" v-model="form.username" id="username" class="form-control"
                 :class="{'is-invalid': errors.username}" placeholder="Enter your username">
          <div v-if="errors.username" class="invalid-feedback">{{ errors.username[0] }}</div>
        </div>

        <div class="mb-3">
          <label for="name">Full Name</label>
          <input type="text" v-model="form.name" id="name" class="form-control"
                 :class="{'is-invalid': errors.name}" placeholder="Full name">
          <div v-if="errors.name" class="invalid-feedback">{{ errors.name[0] }}</div>
        </div>

        <div class="mb-3">
          <label for="student_id">Student ID</label>
          <input type="text" v-model="form.student_id" id="student_id" class="form-control"
                 :class="{'is-invalid': errors.student_id}" placeholder="Student ID">
          <div v-if="errors.student_id" class="invalid-feedback">{{ errors.student_id[0] }}</div>
        </div>

        <div class="mb-3">
          <label for="password">Password</label>
          <input type="password" v-model="form.password" id="password" class="form-control"
                 :class="{'is-invalid': errors.password}" placeholder="Enter password">
          <div v-if="errors.password" class="invalid-feedback">
            {{ Array.isArray(errors.password) ? errors.password[0] : errors.password }}
          </div>
        </div>

        <div v-if="form.password" class="mb-3">
          <div class="d-flex justify-content-between align-items-center">
            <small>Password Strength</small>
            <small v-if="passwordStrength" :class="passwordStrength.color"
                   class="fw-bold">{{ passwordStrength.text }}</small>
          </div>
        </div>

        <div class="mb-3">
          <label for="password2">Confirm Password</label>
          <input type="password" v-model="form.password2" id="password2" class="form-control"
                 :class="{'is-invalid': errors.password2}" placeholder="Confirm password">
          <div v-if="errors.password2" class="invalid-feedback">{{ errors.password2[0] }}</div>
        </div>

        <div v-if="errors.detail" class="alert alert-danger">{{ errors.detail }}</div>

        <button type="submit" class="btn btn-primary w-100 py-2">Register</button>
      </form>

      <hr class="my-4"/>
      <p class="text-center mb-0">
        Already have an account?
        <router-link to="/login">Login here</router-link>
      </p>
    </div>
</template>

<script setup>
import {computed, reactive, ref} from 'vue'; // 引入 computed
import axios from 'axios';
import {useRouter} from 'vue-router';
import VueCropper from 'vue-cropperjs';

// --- State Management ---
const router = useRouter();
const form = reactive({
  username: '',
  password: '',
  password2: '',
  name: '',
  student_id: '',
  user_profile_img: '',
});
const errors = ref({});

// --- Image & Cropper Refs ---
// 改动3: 初始值设为 null
const avatarPreview = ref(null);
const imageToCrop = ref(null);
const fileInput = ref(null);
const cropper = ref(null);

// 改动4: 新增密码强度计算逻辑
const passwordStrength = computed(() => {
  const p = form.password;
  let score = 0;
  if (!p) return null;

  if (p.length >= 8) score++;
  if (p.match(/[a-z]/)) score++;
  if (p.match(/[A-Z]/)) score++;
  if (p.match(/[0-9]/)) score++;
  if (p.match(/[^A-Za-z0-9]/)) score++;

  switch (score) {
    case 0:
    case 1:
    case 2:
      return {text: 'Weak', color: 'text-danger'};
    case 3:
      return {text: 'Medium', color: 'text-warning'};
    case 4:
    case 5:
      return {text: 'Strong', color: 'text-success'};
    default:
      return null;
  }
});

// --- Image Handling Methods ---
const triggerFileInput = () => {
  fileInput.value.click();
};

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (event) => {
      imageToCrop.value = event.target.result;
    };
    reader.readAsDataURL(file);
  }
};

const cropAndSetAvatar = () => {
  if (!cropper.value) return;
  const dataUrl = cropper.value.getCroppedCanvas({
    width: 128,
    height: 128
  }).toDataURL('image/png');
  const pureBase64 = dataUrl.split(',')[1];
  avatarPreview.value = dataUrl;
  form.user_profile_img = pureBase64;
  imageToCrop.value = null;
};

const cancelCrop = () => {
  imageToCrop.value = null;
  fileInput.value.value = '';
};

// --- Form Submission ---
const handleRegister = async () => {
  errors.value = {};
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/register/', form);
    const {access, refresh} = response.data.tokens;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    await router.push('/');
  } catch (err) {
    if (err.response && (err.response.status === 400 || err.response.status === 401)) {
      errors.value = err.response.data;
    } else {
      errors.value = {detail: 'An unexpected error occurred.'};
    }
  }
};
</script>

<style scoped>
.avatar-preview {
  width: 128px;
  height: 128px;
  object-fit: cover;
  border-radius: .25rem;
  border: 1px solid #dee2e6;
  background-color: #fff;
}
</style>
