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
          <UserProfile :avatar-src="avatarSrc" :profile="profile" class="user-profile-component" />
        </section>

        <!-- Barcode Card -->
        <section class="md-card">
          <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>qr_code_2</md-icon>
            <h2 class="md-typescale-headline-small md-m-0">Digital ID Barcode</h2>
          </div>
          <BarcodeDisplay ref="barcodeDisplayRef" @generate="handleGenerate" />
        </section>

        <!-- Quick Actions Card -->
        <section class="md-card md-card-filled">
          <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
            <md-icon>dashboard</md-icon>
            <h2 class="md-typescale-headline-small md-m-0">Quick Actions</h2>
          </div>
          <UserMenu class="user-menu-component" @logout="handleLogout" />
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useHomeUserLogic } from '@home/composables/useHomeUserLogic.js';

// Components
import UserProfile from '@user/components/UserProfile.vue';
import BarcodeDisplay from '@user/components/BarcodeDisplay.vue';
import UserMenu from '@user/components/UserMenu.vue';

// CSS
import '@/assets/styles/home/home-merged.css';

const { profile, barcodeDisplayRef, avatarSrc, handleGenerate, handleLogout } = useHomeUserLogic();
</script>
