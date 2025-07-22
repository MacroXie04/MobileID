<template>
  <!-- 把 index_user.html 的主体粘进来 -->
  <div class="p-4">
    <h1>User Dashboard</h1>
    <p>Hello {{ profile?.name }}!</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { userInfo } from "@/api/auth";

const profile = ref(null);
onMounted(async () => {
  const data = await userInfo();
  profile.value = data?.profile;
});
</script>
