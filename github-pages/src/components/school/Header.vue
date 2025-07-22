<template>
  <div class="container">
    <!-- Header -->
    <div class="header-container">
      <!-- Left: UC Merced Logo -->
      <div class="header-left">
        <a href="/">
          <img :src="ucmLogo" alt="UC Merced Logo" class="logo-image" />
        </a>
      </div>

      <!-- Center: Mobile ID Logo -->
      <div class="header-center">
        <div class="header-logo">
          <img :src="mobileIdLogo" alt="Fingerprint" class="logo-image" />
        </div>
      </div>

      <!-- Right Spacer -->
      <div class="header-right"></div>
    </div>
  </div>

  <div class="header-border"></div>
</template>

<script setup>
import ucmLogo from "@/assets/images/ucm3.png";
import mobileIdLogo from "@/assets/images/mobileid_logo.png";
</script>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  position: relative;
}

.header-left, .header-right {
  flex: 1;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-image {
  height: 60px;
}

.header-border {
  border-top: 1px solid white;
  margin: 0 20px;
}
</style> 