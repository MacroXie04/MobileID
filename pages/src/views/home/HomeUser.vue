<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h1 class="md-typescale-title-medium md-m-0">{{ profile?.name || 'User' }}</h1>
        </div>
        <md-filled-tonal-button @click="handleLogout">
          <md-icon slot="icon">logout</md-icon>
          Sign Out
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="md-content">
      <div class="home-grid md-grid-container md-grid-cols-1 md-grid-cols-2 md-grid-cols-3">
        <!-- User Profile Card -->
        <section class="md-card profile-overview-card">
          <UserProfile
              :avatar-src="avatarSrc"
              :profile="profile"
              class="user-profile-component"
          />
        </section>

        <!-- Barcode Card -->
        <section class="md-card">
          <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>qr_code_2</md-icon>
            <h2 class="md-typescale-headline-small md-m-0">Digital ID Barcode</h2>
          </div>
          <BarcodeDisplay
              ref="barcodeDisplayRef"
              @generate="handleGenerate"
          />
        </section>

        <!-- Quick Actions Card -->
        <section class="md-card md-card-filled">
          <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>dashboard</md-icon>
            <h2 class="md-typescale-headline-small md-m-0">Quick Actions</h2>
          </div>
          <UserMenu
              class="user-menu-component"
              @logout="handleLogout"
          />
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import {onMounted, ref} from "vue";
import {useRouter} from "vue-router";

// Components
import UserProfile from "@/components/user/UserProfile.vue";
import BarcodeDisplay from "@/components/user/BarcodeDisplay.vue";
import UserMenu from "@/components/user/UserMenu.vue";

// Composables
import {useApi} from "@/composables/useApi";
import {useUserInfo} from "@/composables/useUserInfo";
import {baseURL} from "@/config";

// CSS
import '@/assets/css/home-merged.css';

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const profile = ref(null);
const barcodeDisplayRef = ref(null);

// Use composables
const {apiGenerateBarcode} = useApi();
const {avatarSrc, loadAvatar} = useUserInfo();

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
    const {status, barcode, message} = await apiGenerateBarcode();

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
    await fetch(`${baseURL}/authn/logout/`, {
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
