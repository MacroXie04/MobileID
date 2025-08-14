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

    <h4
        id="information_id"
        class="white-h4 profile-info-id"
    >
      {{ profile.information_id }}
    </h4>

    <div id="show-info-button" class="profile-button-container">
      <button
          :disabled="loading || isRefreshingToken"
          class="btn btn-trans btn-trans-default"
          @click="handleGenerate"
      >
        <b>{{
            isRefreshingToken ? "Refreshing Token..." :
                loading ? "Processing…" :
                    "PAY / Check-in"
          }}</b>
      </button>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, toRefs} from 'vue';

// Props
const props = defineProps({
  profile: {
    type: Object,
    required: true
  },
  avatarSrc: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  isRefreshingToken: {
    type: Boolean,
    default: false
  }
});

// Emits
const emit = defineEmits(['generate']);

// Destructure props for reactivity
const {profile, avatarSrc, loading, isRefreshingToken} = toRefs(props);

// State
const showInitials = ref(false);

// Computed
const shouldShowAvatar = computed(() => {
  return avatarSrc.value && !showInitials.value;
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
function handleImageError() {
  showInitials.value = true;
}

// Event handlers
function handleGenerate() {
  emit('generate');
}
</script>

<style scoped>
.profile-section {
  text-align: center;
  margin-top: 2em;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.4);
  transition: transform 0.3s ease-in-out;
}

.profile-initials {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 36px;
  font-weight: 500;
  text-decoration: none;
}

.profile-name {
  margin-top: 0.5em;
  color: white !important;
}

.profile-info-id {
  color: white !important;
  display: none;
}

.profile-button-container {
  margin-top: 1em;
}

/* buttom */
#show-info-button:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease-in-out;
}
</style> 