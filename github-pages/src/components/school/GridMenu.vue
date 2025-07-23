<template>
  <!-- 3 × 3 Grid -->
  <div class="grid-wrapper">
    <div class="grid-container">
      <!-- Row 1 -->
      <a href="/profile/edit" class="btn-grid" @click.prevent="handleEditProfile">
        <i class="fa fa-credit-card fa-2x"></i>
        <p>Add Funds</p>
      </a>
      <a href="/barcode/dashboard" class="btn-grid" @click.prevent="handleBarcodeDashboard">
        <i class="fa fa-money-bill fa-2x"></i>
        <p>Balance</p>
      </a>
      <a id="lost-my-card" href="#" class="btn-grid">
        <i class="fa fa-id-card fa-2x"></i>
        <p>Lost My Card</p>
      </a>

      <!-- Row 2 -->
      <a id="emergency" href="#" class="btn-grid">
        <i class="fa fa-exclamation-triangle fa-2x"></i>
        <p>{{ serverStatus }}</p>
      </a>
      <a id="gym" href="#" class="btn-grid">
        <i class="fa fa-dumbbell fa-2x"></i>
        <p>Gym</p>
      </a>
      <a id="resource" href="#" class="btn-grid">
        <i class="fa fa-info fa-2x"></i>
        <p>Resources</p>
      </a>

      <!-- Row 3 -->
      <a href="https://alynx.ucmerced.edu/" target="_blank" class="btn-grid">
        <i class="fa fa-link fa-2x"></i>
        <p>Alynx</p>
      </a>
      <a href="/logout/" class="btn-grid">
        <i class="fa fa-sign-out-alt fa-2x"></i>
        <p>Log out</p>
      </a>
    </div>
  </div>
</template>

<script setup>
import { toRefs } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// Props
const props = defineProps({
  serverStatus: {
    type: String,
    default: "Emergency"
  }
});

// Destructure props for reactivity
const { serverStatus } = toRefs(props);

// Functions
function handleEditProfile() {
  router.push('/profile/edit');
}

function handleBarcodeDashboard() {
  router.push('/barcode/dashboard');
}
</script>

<style scoped>
.grid-wrapper {
  margin: auto;
  max-width: 320px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding-top: 16px;
}

.btn-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 10px;
  text-decoration: none;
  color: inherit;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;
  min-height: 80px;
}

.btn-grid:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
  text-decoration: none;
  color: inherit;
}

.btn-grid i {
  margin-bottom: 8px;
  color: #bf9c44;
}

.btn-grid p {
  margin: 0;
  font-size: 12px;
  text-align: center;
  color: #bf9c44;
}
</style> 