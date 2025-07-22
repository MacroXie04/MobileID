<template>
  <div class="row gy-3 text-center">
    <div class="col-4">
      <a href="/profile/edit" class="text-decoration-none text-dark d-block" @click.prevent="handleEditProfile">
        <div class="icon-circle"><i class="fa-solid fa-user fa-lg"></i></div>
        <span class="small fw-semibold d-block">Edit Profile</span>
      </a>
    </div>
    <div class="col-4">
      <a href="/barcode/manage" class="text-decoration-none text-dark d-block" @click.prevent="handleManageBarcode">
        <div class="icon-circle"><i class="fa-solid fa-barcode fa-lg"></i></div>
        <span class="small fw-semibold d-block">Manage Barcode</span>
      </a>
    </div>
    <div class="col-4">
      <a href="/logout"
         class="text-decoration-none text-danger d-inline-flex flex-column align-items-center"
         @click.prevent="handleLogout">
        <div class="icon-circle" style="background:rgba(220,53,69,.15);color:#dc3545;">
          <i class="fa-solid fa-right-from-bracket fa-lg"></i>
        </div>
        <span class="small fw-semibold">Log out</span>
      </a>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleManageBarcode() {
  // TODO: Navigate to barcode management page
  console.log('Manage Barcode clicked');
  // router.push('/barcode/manage');
}

function handleLogout() {
  emit('logout');
}
</script>

<style scoped>
.icon-circle {
  width: 64px;
  height: 64px;
  margin: 0 auto .5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(var(--bs-primary-rgb), 0.1);
  color: var(--brand);
  transition: background-color 0.2s;
}

a:hover .icon-circle {
  background: rgba(var(--bs-primary-rgb), 0.15);
}
</style> 