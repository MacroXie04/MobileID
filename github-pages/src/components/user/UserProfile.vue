<template>
  <div class="text-center mb-4">
    <img 
      :src="avatarSrc || defaultAvatar" 
      alt="avatar" 
      class="rounded-circle shadow"
      style="width:112px;height:112px;object-fit:cover;"
      @error="handleImageError"
    >
    <h4 class="mt-3 mb-1 fw-semibold">{{ profile?.name || 'User' }}</h4>
    <p class="text-muted small mb-0">{{ profile?.information_id || 'ID not available' }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import defaultAvatar from '@/assets/images/avatar_placeholder.png';

// Props
const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  }
});

// Avatar helper (base64 → data-URL)
const avatarSrc = computed(() =>
  props.profile?.user_profile_img
    ? `data:image/png;base64,${props.profile.user_profile_img}`
    : ""
);

// Handle image loading error
function handleImageError(event) {
  event.target.src = defaultAvatar;
}
</script>

<style scoped>
/* Component-specific styles if needed */
</style> 