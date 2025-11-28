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
import { emitsDefinition, useUserMenuSetup } from './UserMenu.setup.js';

const emit = defineEmits(emitsDefinition);

const { handleEditProfile, handleLogout } = useUserMenuSetup({ emit });
</script>
