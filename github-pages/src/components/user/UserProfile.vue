<template>
  <div class="text-center mb-4" style="margin-bottom: 0px!important;">
    <img 
      :src="props.avatarSrc || defaultAvatar" 
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
import defaultAvatar from '@/assets/images/avatar_placeholder.png';

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

// Handle image loading error
function handleImageError(event) {
  event.target.src = defaultAvatar;
}
</script>

<style scoped>
/* Component-specific styles if needed */
</style> 