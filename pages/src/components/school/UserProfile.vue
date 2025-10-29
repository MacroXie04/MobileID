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
import {getInitials} from '@/utils/profileUtils.js';

// CSS
import '@/assets/css/school-merged.css';

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

// Handle image loading error
function handleImageError() {
  showInitials.value = true;
}

// Event handlers
function handleGenerate() {
  emit('generate');
}
</script>

