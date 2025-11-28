<template>
  <LoadingOverlay />
  <ServerWakeupOverlay />
  <router-view />
</template>

<script setup>
import { LoadingOverlay, ServerWakeupOverlay, useAppSetup } from './App.setup.js';

useAppSetup();
</script>
