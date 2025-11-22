<!-- pages/src/components/user/UserMenu.vue -->
<template>
  <div class="menu-container">
    <md-list class="user-menu-list">
      <md-list-item class="menu-item" @click="handleEditProfile">
        <template #start>
<md-icon >edit</md-icon>
</template>
        <template #headline>
<div >Edit Profile</div>
</template>
      </md-list-item>
      <md-divider></md-divider>
      <md-list-item class="menu-item menu-item-logout" @click="handleLogout">
        <template #start>
<md-icon >logout</md-icon>
</template>
        <template #headline>
<div >Log out</div>
</template>
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
import '@/assets/css/user-merged.css';

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleLogout() {
  emit('logout');
}
</script>
