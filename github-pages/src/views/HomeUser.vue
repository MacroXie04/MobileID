<template>
  <div class="home-user-container">
    <div class="background-gradient"></div>
    <div class="content-wrapper">
      <div class="profile-card elevation-3">
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

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
const { avatarSrc, loadAvatar } = useUserInfo();

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(() => {
  console.log('HomeUser component mounted');
  // read user info from window.userInfo
  const data = window.userInfo;
  console.log('window.userInfo:', data);
  profile.value = data?.profile;
  console.log('Profile set to:', profile.value);
  
  // Load user avatar
  loadAvatar();
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
/* Material 3 Design System - Enhanced */
.home-user-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--md-sys-color-surface);
  overflow: hidden;
  font-family: 'Roboto', sans-serif; /* Add Material default font */
}

/* Enhanced gradient background */
.background-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(
      ellipse at top left,
      var(--md-sys-color-primary-container) 0%,
      transparent 70%
    ),
    radial-gradient(
      ellipse at bottom right,
      var(--md-sys-color-tertiary-container) 0%,
      transparent 70%
    );
  opacity: 0.1; /* More subtle gradient */
  z-index: 0;
}

.content-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 16px;
}

/* Enhanced card with proper elevation */
.profile-card {
  background: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-extra-large);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  box-shadow: var(--md-sys-elevation-level3); /* Use elevation token */
}

/* Section spacing with MD3 grid */
.user-profile-section {
  padding: 32px 24px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.menu-section {
  padding: 24px; /* Increased padding for better spacing */
}

/* Responsive adjustments with MD3 breakpoints */
@media (max-width: 600px) { /* Standard MD3 breakpoint */
  .content-wrapper {
    padding: 0;
    max-width: 100%;
  }
  
  .profile-card {
    border-radius: 0;
    box-shadow: none;
  }
  
  .user-profile-section {
    padding: 24px 16px;
  }
}

/* Add hover effect for interactive elements */
.profile-card:hover {
  box-shadow: var(--md-sys-elevation-level4);
  transform: translateY(-2px);
}

/* Add focus states for accessibility */
*:focus-visible {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: 2px;
}
</style>
