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
import { useSchoolProfileLogic } from '@school/composables/useSchoolProfileLogic.js';
import '@/assets/styles/school/school-merged.css';

const props = defineProps({
  profile: {
    type: Object,
    required: true,
  },
  avatarSrc: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  isRefreshingToken: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['generate']);

const { shouldShowAvatar, getInitials, handleImageError, handleGenerate } = useSchoolProfileLogic(
  props,
  emit
);
</script>
