<!-- pages/src/components/user/UserMenu.vue -->
<template>
  <div class="menu-container">
    <md-list class="user-menu-list">
      <md-list-item class="menu-item" @click="handleEditProfile">
        <md-icon slot="start">edit</md-icon>
        <div slot="headline">Edit Profile</div>
      </md-list-item>
      <md-divider></md-divider>
      <md-list-item class="menu-item menu-item-logout" @click="handleLogout">
        <md-icon slot="start">logout</md-icon>
        <div slot="headline">Log out</div>
      </md-list-item>
    </md-list>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

// Material Web Components
import '@material/web/icon/icon.js';
import '@material/web/list/list.js';
import '@material/web/list/list-item.js';
import '@material/web/divider/divider.js';

// CSS
import '@/assets/styles/user/user-merged.css';

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleLogout() {
  emit('logout');
}
</script>
