<template>
  <!-- Profile Section -->
  <div class="profile-section">
    <a id="setting-icon" href="/edit_profile/">
      <img
        v-if="shouldShowAvatar"
        :src="avatarSrc"
        alt="User profile picture"
        class="profile-avatar"
        @error="handleImageError"
      />
      <div v-else class="profile-avatar profile-initials">
        {{ getInitials(profile.name) }}
      </div>
    </a>

    <h4 class="white-h4 profile-name">
      {{ profile.name }}
    </h4>

    <transition name="slide-up">
      <h4
        v-show="props.barcodeVisible"
        id="information_id"
        class="white-h4 profile-info-id"
        :aria-hidden="!props.barcodeVisible"
      >
        {{ profile.information_id }}
      </h4>
    </transition>

    <transition name="fade">
      <div
        v-show="!props.barcodeVisible"
        id="show-info-button"
        class="profile-button-container"
        :aria-hidden="props.barcodeVisible"
      >
        <button
          :disabled="loading || isRefreshingToken"
          class="btn btn-trans btn-trans-default"
          @click="handleGenerate"
        >
          <b>{{
            isRefreshingToken ? 'Refreshing Token...' : loading ? 'Processing…' : 'PAY / Check-in'
          }}</b>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import {
  emitsDefinition,
  propsDefinition,
  useSchoolUserProfileSetup,
} from './UserProfile.setup';

const props = defineProps(propsDefinition);
const emit = defineEmits(emitsDefinition);

const { shouldShowAvatar, getInitials, handleImageError, handleGenerate } =
  useSchoolUserProfileSetup({ props, emit });
</script>
