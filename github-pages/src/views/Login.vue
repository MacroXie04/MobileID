<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center" style="min-height:80vh;">
    <div class="card p-4 shadow-sm" style="max-width:500px;width:100%;">
      <h3 class="text-center mb-4">Login</h3>
      <form @submit.prevent="handle">
        <div class="mb-3">
          <label>Username</label>
          <input v-model="username" class="form-control" required />
        </div>
        <div class="mb-3">
          <label>Password</label>
          <input v-model="password" type="password" class="form-control" required />
        </div>
        <div class="text-danger mb-2">{{ error }}</div>
        <button class="btn btn-primary w-100">Login</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { login } from "@/api/auth";
import { useRouter } from "vue-router";

const username = ref("");
const password = ref("");
const error = ref("");
const router = useRouter();

async function handle() {
  error.value = "";
  const res = await login(username.value, password.value);
  if (res.message === "Login successful") {
    location.href = "/";
  } else {
    error.value = res.detail || "Login failed";
  }
}
</script>
