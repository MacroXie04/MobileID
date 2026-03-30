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

    <h4 id="information_id" class="white-h4 profile-info-id">
      {{ profile.information_id }}
    </h4>

    <div id="show-info-button" class="profile-button-container">
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
  </div>
</template>

<script setup>
import {
  emitsDefinition,
  propsDefinition,
  useSchoolUserProfileSetup,
} from './UserProfile.setup.js';

const props = defineProps(propsDefinition);
const emit = defineEmits(emitsDefinition);

const { shouldShowAvatar, getInitials, handleImageError, handleGenerate } =
  useSchoolUserProfileSetup({ props, emit });
</script>
