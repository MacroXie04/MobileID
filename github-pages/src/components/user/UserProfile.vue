<template>
  <div style="text-align: center; margin-bottom: 16px;">
    <img 
      class="profile-picture"
      :src="props.avatarSrc || defaultAvatar" 
      alt="avatar" 
      @error="handleImageError"
    >
    <h4 class="profile-name md-typescale-title-medium">{{ profile?.name || 'User' }}</h4>
    <p class="profile-id md-typescale-body-small">{{ profile?.information_id || 'ID not available' }}</p>
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
@import "@material/web/typography/md-typescale-styles.css";
</style> 