<template>
  <div class="home-school-container">
    <!-- Header Component -->
    <Header />

    <!-- User Profile Component -->
    <UserProfile 
      :profile="profile" 
      :avatar-src="avatarSrc"
      :loading="loading || userInfoLoading"
      :is-refreshing-token="isRefreshingToken"
      @generate="handleGenerate"
    />

    <!-- Barcode Display Component -->
    <BarcodeDisplay ref="barcodeDisplayRef" />

    <!-- Grid Menu Component -->
    <GridMenu :server-status="serverStatus" />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";
import { useRouter } from "vue-router";

// CSS Imports
import "@/assets/css/HomeSchool.css";

// Components
import Header from "@/components/school/Header.vue";
import UserProfile from "@/components/school/UserProfile.vue";
import BarcodeDisplay from "@/components/school/BarcodeDisplay.vue";
import GridMenu from "@/components/school/GridMenu.vue";

// Composables
import { useUserInfo } from "@/composables/useUserInfo";
import { useToken } from "@/composables/useToken";
import { useApi } from "@/composables/useApi";
import { usePdf417 } from "@/composables/usePdf417";

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const loading = ref(false);
const serverStatus = ref("Emergency");
const barcodeDisplayRef = ref(null);

// Use composables
const { profile, avatarSrc, loadAvatar } = useUserInfo();
const { isRefreshingToken } = useToken();
const { apiGenerateBarcode } = useApi();
const { drawPdf417 } = usePdf417();

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(() => {
  // 直接从 window.userInfo 赋值到 profile
  const data = window.userInfo;
  if (data && data.profile) {
    profile.value = data.profile;
  }
  
  // Load user avatar
  loadAvatar();
});

/* ── UI actions with jQuery animations ─────────────────────────────────────── */
async function handleGenerate() {
  loading.value = true;
  serverStatus.value = "Processing";

  try {
    const { status, barcode, message } = await apiGenerateBarcode();
    serverStatus.value = message || "Success";

    if (status === "success" && barcode) {
      // First generate the barcode
      await nextTick();
      
      // Get canvas from BarcodeDisplay component
      const canvas = barcodeDisplayRef.value?.barcodeCanvas;
      if (canvas) {
        drawPdf417(canvas, barcode);
      }

      // Check if elements are already visible (matching original logic)
      const isFaded = window.$('#show-info-button').css('display') === 'none';
      
      if (isFaded) {
        setTimeout(() => {
          window.$('#show-info-button').fadeIn();
        }, 400);
        window.$('#information_id').fadeOut();
        window.$('#qrcode-code').fadeOut();
        window.$('#qrcode-div').fadeOut();
      } else {
        window.$('#show-info-button').fadeOut();

        setTimeout(() => {
          window.$('#qrcode-div').fadeIn();
          window.$('#qrcode-code').fadeIn();
          window.$('#information_id').fadeIn();

          // Reset progress bar width instantly (without animation)
          window.$('.progress-bar').css({
            "transition": "none",
            "width": "100%"
          });

          // Short delay before applying transition again for smooth animation
          setTimeout(() => {
            window.$('.progress-bar').css({
              "transition": "width 10s linear",
              "width": "0%"
            });
          }, 50);

        }, 400);

        // Hide barcode after 10.4 seconds
        setTimeout(() => {
          window.$('#qrcode-div').fadeOut(400);
          window.$('#qrcode-code').fadeOut(400);
          window.$('#information_id').fadeOut(400);
          setTimeout(() => {
            window.$('#show-info-button').fadeIn();
            // Reset server status back to Emergency
            serverStatus.value = "Emergency";
          }, 400);
        }, 10400);
      }
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

