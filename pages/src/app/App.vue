<template>
  <LoadingOverlay />
  <ServerWakeupOverlay />
  <router-view />
</template>

<script setup lang="ts">
import { LoadingOverlay, ServerWakeupOverlay, useAppSetup } from './App.setup';

useAppSetup();
</script>
