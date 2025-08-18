<!-- pages/src/components/user/UserMenu.vue -->
<template>
  <div class="menu-container">
    <md-list class="user-menu-list">
      <md-list-item
          class="menu-item"
          headline="Edit Profile"
          @click="handleEditProfile"
      >
        <md-icon slot="start">edit</md-icon>
      </md-list-item>
      <md-divider></md-divider>
      <md-list-item
          class="menu-item menu-item-logout"
          headline="Log out"
          @click="handleLogout"
      >
        <md-icon slot="start">logout</md-icon>
      </md-list-item>
    </md-list>
  </div>
</template>

<script setup>
import {useRouter} from 'vue-router';

// Material Web Components
import '@material/web/icon/icon.js';
import '@material/web/list/list.js';
import '@material/web/list/list-item.js';
import '@material/web/divider/divider.js';

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleLogout() {
  emit('logout');
}
</script>

<style scoped>
.menu-container {
  padding: 0;
  width: 100%;
}

.user-menu-list {
  --md-list-container-color: transparent;
  padding: 0;
}

.menu-item {
  --md-list-item-label-text-size: 1rem;
  --md-list-item-label-text-weight: 500;
  --md-list-item-hover-state-layer-color: var(--md-sys-color-primary);
  --md-list-item-focus-state-layer-color: var(--md-sys-color-primary);
  --md-list-item-pressed-state-layer-color: var(--md-sys-color-primary);
  border-radius: var(--md-sys-shape-corner-large);
  margin-bottom: 8px;
}

.menu-item:last-child {
  margin-bottom: 0;
}

.menu-item md-icon {
  color: var(--md-sys-color-primary);
}

.menu-item-logout {
  --md-list-item-label-text-color: var(--md-sys-color-error);
  --md-list-item-hover-state-layer-color: var(--md-sys-color-error);
  --md-list-item-focus-state-layer-color: var(--md-sys-color-error);
  --md-list-item-pressed-state-layer-color: var(--md-sys-color-error);
}

.menu-item-logout md-icon {
  color: var(--md-sys-color-error);
}

md-divider {
  margin: 8px 0;
}
</style> 