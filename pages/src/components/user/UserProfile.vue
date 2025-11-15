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
        >
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
import {computed, ref, watch} from 'vue';
import defaultAvatar from '@/assets/images/avatar_placeholder.png';
import {getInitials, handleAvatarError} from '@/utils/user/profileUtils.js';

// CSS
import '@/assets/css/user-merged.css';

// State
const showInitials = ref(false);

// Props
const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  },
  avatarSrc: {
    type: String,
    default: ''
  }
});

// Computed
const avatarUrl = computed(() => {
  if (props.avatarSrc) {
    return props.avatarSrc;
  }
  return null;
});

// Watch for avatarSrc changes
watch(() => props.avatarSrc, (newVal) => {
  if (newVal) {
    showInitials.value = false;
  }
});

// Handle image loading error
function handleImageError(event) {
  handleAvatarError(event, {
    profileName: props.profile?.name,
    placeholderSrc: defaultAvatar,
    onShowInitials: () => { showInitials.value = true; }
  });
}
</script>
