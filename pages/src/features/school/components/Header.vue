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
import { useSchoolHeaderSetup } from './Header.setup.js';

const { ucmLogo, mobileIdLogo } = useSchoolHeaderSetup();
</script>
