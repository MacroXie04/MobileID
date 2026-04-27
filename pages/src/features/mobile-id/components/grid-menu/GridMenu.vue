<template>
  <!-- 3 × 3 Grid -->
  <div class="grid-wrapper">
    <div class="grid-container">
      <!-- Row 1 -->
      <a class="btn-grid" href="/profile/edit" @click.prevent="handleEditProfile">
        <md-icon class="grid-icon">credit_card</md-icon>
        <p>Add Funds</p>
      </a>
      <a class="btn-grid" href="/dashboard" @click.prevent="handleBarcodeDashboard">
        <md-icon class="grid-icon">payments</md-icon>
        <p>Balance</p>
      </a>
      <a id="lost-my-card" class="btn-grid" href="#">
        <md-icon class="grid-icon">badge</md-icon>
        <p>Lost My Card</p>
      </a>

      <!-- Row 2 -->
      <a id="emergency" class="btn-grid" href="#">
        <md-icon class="grid-icon">warning</md-icon>
        <p>{{ serverStatus }}</p>
      </a>
      <a id="gym" class="btn-grid" href="#">
        <md-icon class="grid-icon">fitness_center</md-icon>
        <p>Gym</p>
      </a>
      <a id="resource" class="btn-grid" href="#">
        <md-icon class="grid-icon">info</md-icon>
        <p>Resources</p>
      </a>

      <!-- Row 3 -->
      <a
        class="btn-grid"
        href="https://alynx.ucmerced.edu/"
        rel="noopener noreferrer"
        target="_blank"
      >
        <md-icon class="grid-icon">link</md-icon>
        <p>Alynx</p>
      </a>
      <a class="btn-grid" href="#" @click.prevent="handleLogout">
        <md-icon class="grid-icon">logout</md-icon>
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

<script setup lang="ts">
import { propsDefinition, useGridMenuSetup } from './GridMenu.setup';

const props = defineProps(propsDefinition);

const { serverStatus, handleEditProfile, handleBarcodeDashboard, handleLogout } = useGridMenuSetup({
  props,
});
</script>

<!-- Styles imported via GridMenu.setup.js from school-merged.css -->
