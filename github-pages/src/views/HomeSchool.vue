<template>
  <!-- 把 index.html <body> 部分内容粘进来；以下仅示例 -->
  <div class="p-4">
    <h1>School Dashboard</h1>
    <p>欢迎 {{ profile?.name }}！</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { userInfo, logout } from "@/api/auth";

const profile = ref(null);
onMounted(async () => {
  const data = await userInfo();
  profile.value = data?.profile;
});
</script>
