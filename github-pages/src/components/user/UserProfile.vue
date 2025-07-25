<template>
  <div class="profile-container">
    <!-- Avatar with enhanced Material 3 styling -->
    <div class="avatar-wrapper">
      <div class="avatar-container">
        <img 
          v-if="avatarUrl && !showInitials"
          class="avatar-image"
          :src="avatarUrl" 
          alt="User avatar" 
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
import { ref, computed, watch } from 'vue';
import defaultAvatar from '@/assets/images/avatar_placeholder.png';

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
  // Use avatarSrc if provided, otherwise check if we should show initials
  if (props.avatarSrc) {
    return props.avatarSrc;
  }
  // If no avatarSrc and we have a name, we'll show initials
  return null;
});

// Watch for avatarSrc changes
watch(() => props.avatarSrc, (newVal) => {
  if (newVal) {
    showInitials.value = false;
  }
});

// Get user initials
function getInitials(name) {
  if (!name) return 'U';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

// Handle image loading error
function handleImageError(event) {
  // If we have a name, show initials instead
  if (props.profile?.name) {
    showInitials.value = true;
  } else {
    // Otherwise use placeholder
    event.target.src = defaultAvatar;
  }
}
</script>

<style scoped>
/* Material Design 3 Enhanced Styling */
.profile-container {
  text-align: center;
  position: relative;
  padding: 8px;
}

/* Avatar System - Material 3 */
.avatar-wrapper {
  display: inline-block;
  margin-bottom: 24px;
  position: relative;
}

.avatar-container {
  position: relative;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--md-sys-color-surface-container-high);
  box-shadow: var(--md-sys-elevation-level1);
  transition: all 0.3s var(--md-sys-motion-easing-standard);
}

/* Hover effect for desktop */
@media (hover: hover) {
  .avatar-container:hover {
    transform: scale(1.05);
    box-shadow: var(--md-sys-elevation-level3);
  }
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* Enhanced initials design */
.avatar-initials {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, 
    var(--md-sys-color-primary) 0%, 
    var(--md-sys-color-secondary) 100%
  );
  color: var(--md-sys-color-on-primary);
  font-size: 36px;
  font-weight: 500;
  letter-spacing: 0.1px;
  font-family: 'Roboto', sans-serif;
  user-select: none;
}

/* Subtle ring effect */
.avatar-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    var(--md-sys-color-primary) 0%, 
    var(--md-sys-color-tertiary) 100%
  );
  opacity: 0;
  z-index: -1;
  transition: opacity 0.3s var(--md-sys-motion-easing-standard);
}

.avatar-container:hover .avatar-ring {
  opacity: 0.2;
}

/* Typography - Material 3 Type Scale */
.user-name {
  margin: 0 0 8px 0;
  color: var(--md-sys-color-on-surface);
  font-size: 24px;
  line-height: 32px;
  font-weight: 400;
  letter-spacing: 0;
  font-family: 'Roboto', sans-serif;
}

.user-id {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  letter-spacing: 0.1px;
  font-family: 'Roboto', sans-serif;
}

/* Material 3 Subtle Animation */
@media (prefers-reduced-motion: no-preference) {
  .avatar-container {
    animation: subtle-breathe 4s ease-in-out infinite;
  }
}

@keyframes subtle-breathe {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .avatar-container {
    width: 80px;
    height: 80px;
  }
  
  .avatar-initials {
    font-size: 30px;
  }
  
  .user-name {
    font-size: 20px;
    line-height: 28px;
  }
}
</style> 