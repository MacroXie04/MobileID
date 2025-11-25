<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h3 class="md-typescale-title-medium md-m-0">Edit Profile</h3>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Auto-save Status Toast -->
    <transition name="slide-down">
      <div
        v-if="autoSaveStatus.show"
        :class="[
          'message-toast md-banner',
          autoSaveStatus.type === 'success' ? 'md-banner-success' : 'md-banner-error',
        ]"
      >
        <md-icon>{{ autoSaveStatus.type === 'success' ? 'check_circle' : 'error' }}</md-icon>
        <span class="md-typescale-body-medium">{{ autoSaveStatus.message }}</span>
        <md-icon-button @click="autoSaveStatus.show = false">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Success Message Toast -->
    <transition name="slide-down">
      <div
        v-if="successMessage"
        class="message-toast md-banner md-banner-success"
        style="top: 160px"
      >
        <md-icon>check_circle</md-icon>
        <span class="md-typescale-body-medium">{{ successMessage }}</span>
        <md-icon-button @click="successMessage = ''">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="md-content">
      <section class="md-card md-max-w-xl">
        <form class="md-form" novalidate @submit.prevent="handleSubmit">
          <!-- Avatar Upload Section -->
          <div class="avatar-section md-mb-8">
            <h2 class="md-typescale-headline-small section-title md-mb-6">Profile Photo</h2>

            <div class="avatar-upload-container md-flex md-items-center md-gap-8">
              <div class="avatar-section-center">
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
                    JPG or PNG • Max 5MB • Recommended: Square image
                  </p>
                </div>
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

          <md-divider></md-divider>

          <!-- Personal Information Section -->
          <div class="info-section md-mt-8">
            <h2 class="md-typescale-headline-small section-title md-mb-6">Personal Information</h2>

            <div class="md-form-field">
              <md-outlined-text-field
                v-model="formData.name"
                :error="!!errors.name"
                :error-text="errors.name"
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
                label="Information ID"
                @input="handleFieldChange('information_id')"
                @keyup.enter="!loading && handleSubmit()"
              >
                <md-icon slot="leading-icon">fingerprint</md-icon>
              </md-outlined-text-field>
            </div>
          </div>

          <!-- Auto-save Status Indicator -->
          <div class="auto-save-status md-mt-4 md-p-3 md-rounded-lg md-bg-surface-container-low">
            <div class="md-flex md-items-center md-gap-2">
              <md-icon v-if="autoSaving" class="auto-save-icon">
                <md-circular-progress indeterminate></md-circular-progress>
              </md-icon>
              <md-icon v-else-if="lastSaved" class="auto-save-icon md-text-primary">
                check_circle
              </md-icon>
              <md-icon v-else class="auto-save-icon md-text-on-surface-variant"> schedule </md-icon>
              <span class="md-typescale-body-small">
                {{ getAutoSaveStatusText() }}
              </span>
            </div>
          </div>

          <!-- Error Banner -->
          <transition name="fade">
            <div v-if="errors.general" class="md-banner md-banner-error md-mt-6">
              <md-icon>error_outline</md-icon>
              <span class="md-typescale-body-medium">{{ errors.general }}</span>
            </div>
          </transition>
        </form>
      </section>
    </main>
  </div>

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
      <div class="cropper-tips md-typescale-body-small md-p-4 md-mt-4 md-rounded-lg md-text-center">
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
import { useRouter } from 'vue-router';
import { useProfileEditLogic } from '@user/composables/useProfileEditLogic.js';
import '@/assets/styles/auth/auth-merged.css';

const router = useRouter();

const {
  fileInput,
  cropperDialog,
  loading,
  formData,
  errors,
  successMessage,
  cropperImage,
  showCropper,
  autoSaving,
  lastSaved,
  autoSaveStatus,
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
} = useProfileEditLogic();
</script>
