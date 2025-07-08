<template>
  <div
      class="container mt-5 d-flex justify-content-center align-items-center"
      style="min-height: 80vh;"
  >
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Edit Profile</h3>

      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>

      <form novalidate @submit.prevent="handleUpdate">
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
              Change Avatar
            </button>
            <input
                ref="fileInput"
                accept="image/*"
                class="d-none"
                type="file"
                @change="onFileChange"
            />
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

        <!-- Username (read-only) -->
        <div class="mb-3">
          <label for="username">Username</label>
          <input
              id="username"
              :value="form.username"
              class="form-control"
              disabled
              type="text"
          />
          <small class="form-text text-muted">Username cannot be changed.</small>
        </div>

        <!-- Name -->
        <div class="mb-3">
          <label for="name">Full Name</label>
          <input
              id="name"
              v-model="form.name"
              :class="{ 'is-invalid': errors.name }"
              class="form-control"
              type="text"
          />
          <div v-if="errors.name" class="invalid-feedback">
            {{ errors.name[0] }}
          </div>
        </div>

        <!-- Student / Information ID -->
        <div class="mb-3">
          <label for="information_id">Information&nbsp;ID</label>
          <input
              id="information_id"
              v-model="form.information_id"
              :class="{ 'is-invalid': errors.information_id }"
              class="form-control"
              type="text"
          />
          <div v-if="errors.information_id" class="invalid-feedback">
            {{ errors.information_id[0] }}
          </div>
        </div>

        <div v-if="errors.detail" class="alert alert-danger">
          {{ errors.detail }}
        </div>

        <div class="d-grid gap-2">
          <button :disabled="isSaving" class="btn btn-primary py-2" type="submit">
            {{ isSaving ? "Saving..." : "Save Changes" }}
          </button>
          <router-link class="btn btn-secondary" to="/">Back to Home</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from "vue";
import {useRouter} from "vue-router";
import apiClient from "@/api";
import VueCropper from "vue-cropperjs";

// -------------------- State --------------------
const router = useRouter();
const form = reactive({
  username: "",
  name: "",
  information_id: "",
});
const originalData = ref({});
const errors = ref({});
const successMessage = ref("");
const isSaving = ref(false);

// -------------- Avatar & Cropper ---------------
const avatarPreview = ref(null);
const imageToCrop = ref(null);
const fileInput = ref(null);
const cropper = ref(null);
let newAvatarData = null;

// ------------------ Life-cycle -----------------
onMounted(async () => {
  try {
    const {data} = await apiClient.get("/me/");
    form.username = data.username;
    form.name = data.userprofile?.name || "";
    form.information_id = data.userprofile?.information_id || "";
    originalData.value = {...data.userprofile}; // name, information_id, user_profile_img
    avatarPreview.value = `data:image/png;base64,${data.userprofile?.user_profile_img || ""}`;
  } catch (err) {
    console.error("Failed to load profile", err);
    errors.value = {detail: "Could not load your profile data."};
  }
});

// --------------- File / Cropper ----------------
const triggerFileInput = () => fileInput.value.click();

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (evt) => (imageToCrop.value = evt.target.result);
  reader.readAsDataURL(file);
};

const cancelCrop = () => (imageToCrop.value = null);

const cropAndSetAvatar = () => {
  if (!cropper.value) return;
  const dataUrl = cropper.value
      .getCroppedCanvas({width: 128, height: 128})
      .toDataURL("image/png");
  newAvatarData = dataUrl.split(",")[1]; // 去掉前缀
  avatarPreview.value = dataUrl;
  imageToCrop.value = null;
};

// ---------------- Form Submit ------------------
const handleUpdate = async () => {
  isSaving.value = true;
  errors.value = {};
  successMessage.value = "";

  const userprofilePayload = {};
  if (form.name !== originalData.value.name) userprofilePayload.name = form.name;
  if (form.information_id !== originalData.value.information_id)
    userprofilePayload.information_id = form.information_id;
  if (newAvatarData) userprofilePayload.user_profile_img = newAvatarData;

  if (Object.keys(userprofilePayload).length === 0) {
    successMessage.value = "No changes to save.";
    isSaving.value = false;
    return;
  }

  try {
    const {data} = await apiClient.patch("/me/", {
      userprofile: userprofilePayload,
    });

    originalData.value = {...data.userprofile};
    newAvatarData = null;
    successMessage.value = "Profile updated successfully!";
  } catch (err) {
    if (err.response?.status === 400) {
      const nested = err.response.data.userprofile || {};
      errors.value = {...nested, detail: err.response.data.detail};
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