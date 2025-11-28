<template>
  <!-- 3 × 3 Grid -->
  <div class="grid-wrapper">
    <div class="grid-container">
      <!-- Row 1 -->
      <a class="btn-grid" href="/profile/edit" @click.prevent="handleEditProfile">
        <i class="fa fa-credit-card fa-2x"></i>
        <p>Add Funds</p>
      </a>
      <a class="btn-grid" href="/dashboard" @click.prevent="handleBarcodeDashboard">
        <i class="fa fa-money-bill fa-2x"></i>
        <p>Balance</p>
      </a>
      <a id="lost-my-card" class="btn-grid" href="#">
        <i class="fa fa-id-card fa-2x"></i>
        <p>Lost My Card</p>
      </a>

      <!-- Row 2 -->
      <a id="emergency" class="btn-grid" href="#">
        <i class="fa fa-exclamation-triangle fa-2x"></i>
        <p>{{ serverStatus }}</p>
      </a>
      <a id="gym" class="btn-grid" href="#">
        <i class="fa fa-dumbbell fa-2x"></i>
        <p>Gym</p>
      </a>
      <a id="resource" class="btn-grid" href="#">
        <i class="fa fa-info fa-2x"></i>
        <p>Resources</p>
      </a>

      <!-- Row 3 -->
      <a
        class="btn-grid"
        href="https://alynx.ucmerced.edu/"
        rel="noopener noreferrer"
        target="_blank"
      >
        <i class="fa fa-link fa-2x"></i>
        <p>Alynx</p>
      </a>
      <a class="btn-grid" href="#" @click.prevent="handleLogout">
        <i class="fa fa-sign-out-alt fa-2x"></i>
        <p>Log out</p>
      </a>
    </div>

    <!-- Scanner Detection Status -->
    <transition name="fade">
      <div
        v-if="scannerDetectionEnabled && (isDetectionActive || scannerDetected)"
        class="detection-status"
        :class="{ detected: scannerDetected }"
      >
        <md-icon>{{ scannerDetected ? 'check_circle' : 'sensors' }}</md-icon>
        <span>{{ scannerDetected ? 'Scanner detected!' : 'Scanner detection active' }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { propsDefinition, useGridMenuSetup } from './GridMenu.setup.js';

const props = defineProps(propsDefinition);

const { serverStatus, handleEditProfile, handleBarcodeDashboard, handleLogout } = useGridMenuSetup({
  props,
});
</script>

<!-- Styles imported via GridMenu.setup.js from school-merged.css -->
