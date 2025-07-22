<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="card p-4 mobile-card">
      <!-- User Profile Section -->
      <UserProfile :profile="profile" />

      <!-- Barcode Display Section -->
      <BarcodeDisplay ref="barcodeDisplayRef" @generate="handleGenerate" />

      <!-- User Menu Section -->
      <UserMenu @logout="handleLogout" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

// CSS Imports
import "bootstrap/dist/css/bootstrap.min.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "@/assets/css/mobileid_user.css";

// Components
import UserProfile from "@/components/user/UserProfile.vue";
import BarcodeDisplay from "@/components/user/BarcodeDisplay.vue";
import UserMenu from "@/components/user/UserMenu.vue";

// Composables
import { useApi } from "@/composables/useApi";

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const profile = ref(null);
const barcodeDisplayRef = ref(null);

// Use composables
const { apiGenerateBarcode } = useApi();

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
/* Additional component-specific styles if needed */
</style>
