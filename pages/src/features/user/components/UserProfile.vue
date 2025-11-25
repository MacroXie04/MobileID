<template>
  <div class="profile-container">
    <!-- Avatar with enhanced Material 3 styling -->
    <div class="avatar-wrapper">
      <div class="avatar-container">
        <img
          v-if="avatarUrl && !showInitials"
          :src="avatarUrl"
          alt="User avatar"
          class="avatar-image"
          @error="handleImageError"
        />
        <div v-else class="avatar-initials">
          {{ getInitials(profile?.name) }}
        </div>
        <!-- MD3 Subtle ring effect -->
        <div class="avatar-ring"></div>
      </div>
    </div>

    <!-- User Information with MD3 Typography -->
    <h2 class="user-name">
      {{ profile?.name || 'User' }}
    </h2>
    <p class="user-id">
      {{ profile?.information_id || 'ID not available' }}
    </p>
  </div>
</template>

<script setup>
import { useUserProfileComponentLogic } from '@user/composables/useUserProfileComponentLogic.js';

// CSS
import '@/assets/styles/user/user-merged.css';

// Props
const props = defineProps({
  profile: {
    type: Object,
    default: () => ({}),
  },
  avatarSrc: {
    type: String,
    default: '',
  },
});

const { showInitials, avatarUrl, getInitials, handleImageError } =
  useUserProfileComponentLogic(props);
</script>
