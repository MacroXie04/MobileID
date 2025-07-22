<template>
  <!-- Profile Section -->
  <div class="profile-section">
    <a href="/edit_profile/" id="setting-icon">
      <img
        :src="avatarSrc"
        class="profile-avatar"
        alt="User profile picture"
      />
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
        class="btn btn-trans btn-trans-default"
        :disabled="loading || isRefreshingToken"
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
import { toRefs } from 'vue';

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
const { profile, avatarSrc, loading, isRefreshingToken } = toRefs(props);

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

/* 按钮悬停效果 */
#show-info-button:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease-in-out;
}
</style> 