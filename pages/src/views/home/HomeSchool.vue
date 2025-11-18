<template>
  <div class="home-school-container">
    <!-- Header Component -->
    <Header/>

    <!-- User Profile Component -->
    <UserProfile
        :avatar-src="avatarSrc"
        :is-refreshing-token="isRefreshingToken"
        :loading="loading || userInfoLoading"
        :profile="profile"
        @generate="handleGenerate"
    />

    <!-- Barcode Display Component -->
    <BarcodeDisplay ref="barcodeDisplayRef"/>

    <!-- Grid Menu Component -->
    <GridMenu :server-status="serverStatus"/>
  </div>
</template>

<script setup>
import {nextTick, onMounted, ref, watch} from "vue";
import {useRouter} from "vue-router";

// CSS Imports
import "@/assets/css/HomeSchool.css";
// Import Font Awesome for this page (needed for GridMenu component)
import '@fortawesome/fontawesome-free/css/all.min.css';

// Components
import Header from "@/components/school/Header.vue";
import UserProfile from "@/components/school/UserProfile.vue";
import BarcodeDisplay from "@/components/school/BarcodeDisplay.vue";
import GridMenu from "@/components/school/GridMenu.vue";

// Composables
import {useUserInfo} from "@/composables/user/useUserInfo";
import {useToken} from "@/composables/auth/useToken";
import {useApi} from "@/composables/common/useApi";
import {usePdf417} from "@/composables/barcode/usePdf417";
import {animateBarcodeSequence} from "@/utils/common/jQueryAnimations.js";

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const loading = ref(false);
const serverStatus = ref("Emergency");
const barcodeDisplayRef = ref(null);

// Use composables
const {profile, avatarSrc: defaultAvatarSrc, loadAvatar} = useUserInfo();
const {isRefreshingToken} = useToken();
const {apiGenerateBarcode, apiGetActiveProfile} = useApi();
const {drawPdf417} = usePdf417();

// Create a new ref for avatarSrc that can be overridden
const avatarSrc = ref(defaultAvatarSrc.value);

// Watch for changes in defaultAvatarSrc
watch(defaultAvatarSrc, (newValue) => {
  avatarSrc.value = newValue;
});

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(async () => {
  // directly assign window.userInfo to profile
  const data = window.userInfo;
  if (data && data.profile) {
    profile.value = data.profile;
  }

  // Load user avatar
  loadAvatar();

  // Check for active profile (for School users with barcode profile association)
  try {
    console.log('HomeSchool: Fetching active profile...');
    const response = await apiGetActiveProfile();
    console.log('HomeSchool: Active profile response:', response);

    if (response && response.profile_info) {
      console.log('HomeSchool: Profile info found:', response.profile_info);
      console.log('HomeSchool: Current profile before update:', profile.value);

      // Override with barcode profile info
      profile.value = {
        name: response.profile_info.name,
        information_id: response.profile_info.information_id
      };

      // Update avatar if provided
      if (response.profile_info.avatar_data) {
        console.log('HomeSchool: Updating avatar with profile data');
        avatarSrc.value = response.profile_info.avatar_data;
      }

      console.log('HomeSchool: Profile updated to:', profile.value);
      console.log('HomeSchool: Avatar updated to:', avatarSrc.value?.substring(0, 50) + '...');
    } else {
      console.log('HomeSchool: No active profile info returned, using default profile');
    }
  } catch (error) {
    console.error('HomeSchool: Failed to load active profile:', error);
  }
});

/* ── UI actions with jQuery animations ─────────────────────────────────────── */
async function handleGenerate() {
  loading.value = true;
  serverStatus.value = "Processing";

  try {
    const {status, barcode, message, profile_info} = await apiGenerateBarcode();
    serverStatus.value = message || "Success";

    if (status === "success" && barcode) {
      // Update profile if profile_info is returned (for School users with associate_user_profile_with_barcode)
      if (profile_info) {
        console.log('HomeSchool: Generate barcode returned profile info:', profile_info);
        profile.value = {
          name: profile_info.name,
          information_id: profile_info.information_id
        };
        // Update avatar if provided
        if (profile_info.avatar_data) {
          console.log('HomeSchool: Updating avatar from generate barcode response');
          avatarSrc.value = profile_info.avatar_data;
        }
        console.log('HomeSchool: Profile updated from generate response to:', profile.value);
      } else {
        console.log('HomeSchool: No profile_info in generate barcode response');
      }
      // First generate the barcode
      await nextTick();

      // Get canvas from BarcodeDisplay component
      const canvas = barcodeDisplayRef.value?.barcodeCanvas;
      if (canvas) {
        drawPdf417(canvas, barcode);
      }

      // Use animation utility for barcode sequence
      await animateBarcodeSequence({
        displayDuration: 10000,
        fadeInDuration: 400,
        fadeOutDuration: 400
      });

      // Reset server status back to Emergency after animation completes
      serverStatus.value = "Emergency";
    }
  } catch (err) {
    // Handle different types of errors
    if (err.message.includes("Token refresh failed") || err.message.includes("Max retries exceeded")) {
      console.log("Token refresh failed or max retries exceeded, redirecting to login page");
      return;
    } else if (err.message.includes("Network error")) {
      serverStatus.value = "Network Error";
      console.error("Network error:", err.message);
    } else {
      serverStatus.value = "Error";
      console.error("Barcode generation error:", err);
    }
  } finally {
    loading.value = false;
  }
}
</script>