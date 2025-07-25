<template>
  <div class="home-user-container">
    <div class="background-gradient"></div>
    <div class="content-wrapper">
      <md-elevation :level="3" class="profile-card">
        <!-- User Profile Section -->
        <UserProfile 
          class="user-profile-section" 
          :profile="profile" 
          :avatar-src="avatarSrc" 
        />

        <!-- Barcode Display Section -->
        <BarcodeDisplay 
          ref="barcodeDisplayRef" 
          @generate="handleGenerate" 
        />

        <!-- User Menu Section -->
        <UserMenu 
          class="menu-section" 
          @logout="handleLogout" 
        />
      </md-elevation>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

// Material Web Components
import '@material/web/elevation/elevation.js';

// CSS Imports
import '@/assets/css/HomeUser.css';

// Components
import UserProfile from "@/components/user/UserProfile.vue";
import BarcodeDisplay from "@/components/user/BarcodeDisplay.vue";
import UserMenu from "@/components/user/UserMenu.vue";

// Composables
import { useApi } from "@/composables/useApi";
import { useUserInfo } from "@/composables/useUserInfo";

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const profile = ref(null);
const barcodeDisplayRef = ref(null);

// Use composables
const { apiGenerateBarcode } = useApi();
const { avatarSrc } = useUserInfo();

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(() => {
  // read user info from window.userInfo
  const data = window.userInfo;
  profile.value = data?.profile;
});

/* ── barcode generation ─────────────────────────────────────────────────── */
async function handleGenerate() {
  const barcodeDisplay = barcodeDisplayRef.value;
  if (!barcodeDisplay) return;

  barcodeDisplay.startProcessing();

  try {
    const { status, barcode, message } = await apiGenerateBarcode();

    if (status === "success" && barcode) {
      barcodeDisplay.drawPDF417(barcode);
      barcodeDisplay.showSuccess(message || 'Success');
    } else {
      barcodeDisplay.showError(message || 'Server Error');
    }
  } catch (err) {
    // Handle different types of errors
    if (err.message.includes("Token refresh failed") || err.message.includes("Max retries exceeded")) {
      console.log("Token refresh failed or max retries exceeded, redirecting to login page");
      router.push('/login');
      return;
    } else if (err.message.includes("Network error")) {
      barcodeDisplay.showError("Network Error");
      console.error("Network error:", err.message);
    } else {
      barcodeDisplay.showError("Error");
      console.error("Barcode generation error:", err);
    }
  }
}

/* ── logout ─────────────────────────────────────────────────────────────── */
async function handleLogout() {
  try {
    // Call logout API
    await fetch("http://127.0.0.1:8000/authn/logout/", {
      method: "POST",
      credentials: "include"
    });
    
    // Clear window.userInfo
    window.userInfo = null;
    
    // Navigate to login
    router.push('/login');
  } catch (error) {
    console.error("Logout error:", error);
    // Even if logout API fails, clear local data and redirect
    window.userInfo = null;
    router.push('/login');
  }
}
</script>

<style scoped>
/* Material 3 Design System */
.home-user-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--md-sys-color-surface);
  overflow: hidden;
}

/* Subtle gradient background */
.background-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    ellipse at top left,
    var(--md-sys-color-primary-container) 0%,
    transparent 50%
  ),
  radial-gradient(
    ellipse at bottom right,
    var(--md-sys-color-tertiary-container) 0%,
    transparent 50%
  );
  opacity: 0.3;
  z-index: 0;
}

.content-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 16px;
}

.profile-card {
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-extra-large);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

/* Hover effect for card */
@media (hover: hover) {
  .profile-card:hover {
    transform: translateY(-2px);
  }
}

/* Section spacing */
.user-profile-section {
  padding: 32px 24px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.menu-section {
  padding: 16px;
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .content-wrapper {
    padding: 8px;
  }
  
  .user-profile-section {
    padding: 24px 16px 16px;
  }
}
</style>
