<template>
  <div class="menu-grid">
    <div class="menu-item" @click="handleEditProfile">
      <div class="icon-circle">
        <md-icon>person</md-icon>
      </div>
      <div class="md-typescale-label-medium">Edit Profile</div>
    </div>
    <div class="menu-item" @click="handleManageBarcode">
      <div class="icon-circle">
        <md-icon>qr_code_scanner</md-icon>
      </div>
      <div class="md-typescale-label-medium">Manage Barcode</div>
    </div>
    <div class="menu-item" @click="handleLogout">
      <div class="icon-circle" style="color: var(--md-sys-color-error); background: rgba(220,53,69,0.1);">
        <md-icon>logout</md-icon>
      </div>
      <div class="md-typescale-label-medium" style="color: var(--md-sys-color-error);">Log out</div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import '@material/web/icon/icon.js';
import "@material/web/typography/md-typescale-styles.css";

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleManageBarcode() {
  router.push('/barcode/dashboard');
}

function handleLogout() {
  emit('logout');
}
</script>

<style scoped>
</style> 