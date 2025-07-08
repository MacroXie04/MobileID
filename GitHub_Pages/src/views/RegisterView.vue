<template>
  <div
    class="container mt-5 d-flex justify-content-center align-items-center"
    style="min-height: 80vh;"
  >
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Create Account</h3>

      <form novalidate @submit.prevent="handleRegister">
        <!-- Avatar -->
        <div class="mb-3 text-center">
          <img
            v-if="avatarPreview"
            :src="avatarPreview"
            alt="Avatar Preview"
            class="avatar-preview mb-2"
          />

          <div v-if="!imageToCrop">
            <button
              class="btn btn-outline-secondary w-100"
              type="button"
              @click="triggerFileInput"
            >
              Select Avatar
            </button>
            <input
              ref="fileInput"
              accept="image/*"
              class="d-none"
              type="file"
              @change="onFileChange"
            />
          </div>

          <div
            v-if="errors.user_profile_img"
            class="invalid-feedback d-block text-start"
          >
            {{ errors.user_profile_img[0] }}
          </div>
        </div>

        <!-- Cropper -->
        <div v-if="imageToCrop" class="mb-3">
          <vue-cropper
            ref="cropper"
            :aspect-ratio="1"
            :src="imageToCrop"
            style="height: 400px;"
            view-mode="1"
          />
          <div class="d-flex justify-content-center mt-2">
            <button
              class="btn btn-primary"
              type="button"
              @click="cropAndSetAvatar"
            >
              Crop &amp; Use
            </button>
            <button class="btn btn-link" type="button" @click="cancelCrop">
              Cancel
            </button>
          </div>
        </div>

        <!-- Username -->
        <div class="mb-3">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="form.username"
            :class="{ 'is-invalid': errors.username }"
            class="form-control"
            placeholder="Enter your username"
            type="text"
          />
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username[0] }}
          </div>
        </div>

        <!-- Full Name -->
        <div class="mb-3">
          <label for="name">Full Name</label>
          <input
            id="name"
            v-model="form.name"
            :class="{ 'is-invalid': errors.name }"
            class="form-control"
            placeholder="Full name"
            type="text"
          />
          <div v-if="errors.name" class="invalid-feedback">
            {{ errors.name[0] }}
          </div>
        </div>

        <!-- Information ID -->
        <div class="mb-3">
          <label for="information_id">Information&nbsp;ID</label>
          <input
            id="information_id"
            v-model="form.information_id"
            :class="{ 'is-invalid': errors.information_id }"
            class="form-control"
            placeholder="Information ID"
            type="text"
          />
          <div v-if="errors.information_id" class="invalid-feedback">
            {{ errors.information_id[0] }}
          </div>
        </div>

        <!-- Password -->
        <div class="mb-3">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            :class="{ 'is-invalid': errors.password }"
            class="form-control"
            placeholder="Enter password"
            type="password"
          />
          <div v-if="errors.password" class="invalid-feedback">
            {{ Array.isArray(errors.password) ? errors.password[0] : errors.password }}
          </div>
        </div>

        <!-- Strength Indicator -->
        <div v-if="form.password" class="mb-3">
          <div class="d-flex justify-content-between align-items-center">
            <small>Password Strength</small>
            <small
              v-if="passwordStrength"
              :class="passwordStrength.color"
              class="fw-bold"
            >{{ passwordStrength.text }}</small>
          </div>
        </div>

        <!-- Confirm Password -->
        <div class="mb-3">
          <label for="password2">Confirm Password</label>
          <input
            id="password2"
            v-model="form.password2"
            :class="{ 'is-invalid': errors.password2 }"
            class="form-control"
            placeholder="Confirm password"
            type="password"
          />
          <div v-if="errors.password2" class="invalid-feedback">
            {{ errors.password2[0] }}
          </div>
        </div>

        <div v-if="errors.detail" class="alert alert-danger">
          {{ errors.detail }}
        </div>

        <button class="btn btn-primary w-100 py-2" type="submit">
          Register
        </button>
      </form>

      <hr class="my-4" />
      <p class="text-center mb-0">
        Already have an account?
        <router-link to="/login">Login here</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import apiClient from "@/api";
import VueCropper from "vue-cropperjs";

// ---------------- State ----------------
const router = useRouter();
const form = reactive({
  username: "",
  password: "",
  password2: "",
  name: "",
  information_id: "",
  user_profile_img: "",
});
const errors = ref({});

// ------------- Avatar / Cropper ---------
const avatarPreview = ref(null);
const imageToCrop = ref(null);
const fileInput = ref(null);
const cropper = ref(null);

const triggerFileInput = () => fileInput.value.click();

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file || !file.type.startsWith("image/")) return;
  const reader = new FileReader();
  reader.onload = (evt) => (imageToCrop.value = evt.target.result);
  reader.readAsDataURL(file);
};

const cropAndSetAvatar = () => {
  if (!cropper.value) return;
  const dataUrl = cropper.value
    .getCroppedCanvas({ width: 128, height: 128 })
    .toDataURL("image/png");
  form.user_profile_img = dataUrl.split(",")[1]; // 纯 base64
  avatarPreview.value = dataUrl;
  imageToCrop.value = null;
};

const cancelCrop = () => {
  imageToCrop.value = null;
  fileInput.value.value = "";
};

// ------------- Password Strength --------
const passwordStrength = computed(() => {
  const p = form.password;
  if (!p) return null;
  let score = 0;
  if (p.length >= 8) score++;
  if (/[a-z]/.test(p)) score++;
  if (/[A-Z]/.test(p)) score++;
  if (/[0-9]/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p)) score++;

  if (score <= 2) return { text: "Weak", color: "text-danger" };
  if (score === 3) return { text: "Medium", color: "text-warning" };
  return { text: "Strong", color: "text-success" };
});

// -------------- Register ----------------
const handleRegister = async () => {
  errors.value = {};
  try {
    const { data } = await apiClient.post("/register/", form);
    localStorage.setItem("access_token", data.tokens.access);
    localStorage.setItem("refresh_token", data.tokens.refresh);
    await router.push("/");
  } catch (err) {
    if (err.response?.status === 400) {
      errors.value = err.response.data;
    } else {
      errors.value = { detail: "An unexpected error occurred." };
    }
  }
};
</script>

<style scoped>
.avatar-preview {
  width: 128px;
  height: 128px;
  object-fit: cover;
  border-radius: 0.25rem;
  border: 1px solid #dee2e6;
  background-color: #fff;
}
</style>