<template>
  <section class="dashboard-card profile-tab-card">
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>account_circle</md-icon>
      </div>
      <div class="header-text">
        <h2 class="md-typescale-headline-small md-m-0">Profile</h2>
      </div>
      <transition name="fade">
        <div v-if="autoSaving" class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto">
          <md-circular-progress indeterminate></md-circular-progress>
          <span class="md-typescale-body-small">Saving...</span>
        </div>
      </transition>
    </div>

    <form class="profile-tab-form" novalidate @submit.prevent="handleSubmit">
      <div class="profile-tab-grid">
        <div class="profile-panel">
          <div class="section-heading">
            <div class="section-title">
              <md-icon>photo_camera</md-icon>
              <div>
                <p class="md-typescale-title-small md-m-0">Profile Photo</p>
              </div>
            </div>
          </div>

          <div class="avatar-upload-container md-flex md-items-center md-gap-6">
            <div class="avatar-wrapper md-avatar-xl" @click="selectImage">
              <img :src="getAvatarSrc()" alt="Profile" class="avatar-image" />
              <div class="avatar-overlay">
                <md-icon>photo_camera</md-icon>
                <span class="md-typescale-label-medium">Change Photo</span>
              </div>
            </div>

            <div class="avatar-info">
              <p class="md-typescale-body-medium md-m-0">Click to upload a new profile photo</p>
              <p class="md-typescale-body-small md-m-0 md-mt-1">
                Recommended: Square image for best fit across the dashboard.
              </p>
            </div>
          </div>

          <input
            ref="fileInput"
            accept="image/jpeg,image/jpg,image/png"
            class="hidden-input"
            type="file"
            @change="handleFileSelect"
          />

          <transition name="fade">
            <div v-if="errors.user_profile_img" class="md-banner md-banner-error md-mt-4">
              <md-icon>error</md-icon>
              <span>{{ errors.user_profile_img }}</span>
            </div>
          </transition>
        </div>

        <div class="profile-panel">
          <div class="section-heading">
            <div class="section-title">
              <md-icon>badge</md-icon>
              <div>
                <p class="md-typescale-title-small md-m-0">Personal Information</p>
              </div>
            </div>
          </div>

          <div class="md-form-field profile-inputs">
            <md-outlined-text-field
              v-model="formData.name"
              :error="!!errors.name"
              :error-text="errors.name"
              :disabled="loading"
              label="Full Name"
              @input="handleFieldChange('name')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">badge</md-icon>
            </md-outlined-text-field>

            <md-outlined-text-field
              v-model="formData.information_id"
              :error="!!errors.information_id"
              :error-text="errors.information_id"
              :disabled="loading"
              label="Information ID"
              @input="handleFieldChange('information_id')"
              @keyup.enter="!loading && handleSubmit()"
            >
              <md-icon slot="leading-icon">fingerprint</md-icon>
            </md-outlined-text-field>
          </div>
        </div>
      </div>

      <div class="profile-footer md-flex md-items-center md-gap-3 md-mt-4">
        <div class="save-indicator md-flex md-items-center md-gap-2">
          <template v-if="autoSaving">
            <md-circular-progress indeterminate></md-circular-progress>
          </template>
          <template v-else-if="lastSaved">
            <md-icon class="auto-save-icon md-text-primary">check_circle</md-icon>
          </template>
          <template v-else>
            <md-icon class="auto-save-icon md-text-on-surface-variant">schedule</md-icon>
          </template>
          <span class="md-typescale-body-small">
            {{ getAutoSaveStatusText() }}
          </span>
        </div>

        <transition name="fade">
          <div v-if="errors.general" class="md-banner md-banner-error profile-error-banner">
            <md-icon>error_outline</md-icon>
            <span class="md-typescale-body-medium">{{ errors.general }}</span>
          </div>
        </transition>
      </div>
    </form>

    <!-- Cropper Dialog -->
    <md-dialog
      ref="cropperDialog"
      :open="showCropper"
      class="cropper-dialog"
      @close="handleDialogClose"
    >
      <div slot="headline">
        <md-icon>crop</md-icon>
        Crop Your Photo
      </div>
      <form slot="content" class="cropper-content" method="dialog">
        <div ref="cropperContainer" class="cropper-container md-rounded-lg">
          <img ref="cropperImage" alt="Image to crop" class="cropper-image" />
        </div>
        <div
          class="cropper-tips md-typescale-body-small md-p-4 md-mt-4 md-rounded-lg md-text-center"
        >
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
  </section>
</template>

<script setup>
import { useProfileEditLogic } from '@user/composables/useProfileEditLogic.js';
import '@/assets/styles/auth/auth-merged.css';

const {
  fileInput,
  cropperDialog,
  loading,
  formData,
  errors,
  cropperImage,
  showCropper,
  autoSaving,
  lastSaved,
  getAutoSaveStatusText,
  getAvatarSrc,
  selectImage,
  handleFileSelect,
  applyCrop,
  cancelCrop,
  handleDialogClose,
  handleFieldChange,
  handleSubmit,
  resetCrop,
} = useProfileEditLogic({ redirectOnSubmit: false });
</script>

<style scoped>
.profile-tab-card {
  padding: var(--md-sys-spacing-5);
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-4);
}

.profile-tab-form {
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-4);
}

.profile-tab-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: var(--md-sys-spacing-5);
  align-items: start;
}

.profile-panel {
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-large);
  padding: var(--md-sys-spacing-4);
  box-shadow: var(--md-elevation-1);
  display: flex;
  flex-direction: column;
  gap: var(--md-sys-spacing-3);
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
}

.section-title md-icon {
  color: var(--md-sys-color-primary);
}

.section-subtitle {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-body-small-size);
}

.avatar-upload-container {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--md-sys-spacing-4);
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-large);
  padding: var(--md-sys-spacing-4);
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  overflow: hidden;
  border-radius: 24px;
  box-shadow: var(--md-elevation-2);
}

.avatar-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 520px;
  color: var(--md-sys-color-on-surface);
}

.avatar-info .md-typescale-body-small {
  color: var(--md-sys-color-on-surface-variant);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.45);
  color: white;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.profile-inputs md-outlined-text-field {
  width: 100%;
}

.profile-inputs md-outlined-text-field + md-outlined-text-field {
  margin-top: var(--md-sys-spacing-3);
}

.profile-footer {
  flex-wrap: wrap;
}

.profile-error-banner {
  flex: 1;
  min-width: 260px;
}

.auto-save-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 960px) {
  .profile-tab-grid {
    grid-template-columns: 1fr;
  }

  .avatar-upload-container {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .avatar-info {
    align-items: center;
  }
}
</style>
