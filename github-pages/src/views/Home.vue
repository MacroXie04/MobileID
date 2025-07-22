<!-- src/views/Home.vue -->
<template>
  <div v-if="loading" class="text-center mt-5">Loading…</div>

  <!-- 根据用户组渲染 -->
  <HomeSchool v-else-if="groups.includes('School')" />
  <HomeUser   v-else-if="groups.includes('User')"   />
  <div v-else class="text-center mt-5">
    未知用户组，请联系管理员
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { userInfo } from "@/api/auth";
import HomeSchool from "@/views/HomeSchool.vue";
import HomeUser   from "@/views/HomeUser.vue";

const loading = ref(true);
const groups  = ref([]);

onMounted(async () => {
  const data = await userInfo();
  if (data) groups.value = data.groups;
  loading.value = false;
});
</script>