<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 500px; width: 100%;">
      <h3 class="text-center mb-4">Login</h3>

      <form novalidate @submit.prevent="handleLogin">

        <div v-if="errors.detail" class="alert alert-danger">
          {{ errors.detail }}
        </div>

        <div class="mb-3">
          <label class="form-label" for="username">Username</label>
          <input
              id="username"
              v-model="username"
              :class="{ 'is-invalid': errors.username }"
              class="form-control"
              placeholder="Enter your username"
              required
              type="text"
          />
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username[0] }}
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label" for="password">Password</label>
          <input
              id="password"
              v-model="password"
              :class="{ 'is-invalid': errors.password }"
              class="form-control"
              placeholder="Enter your password"
              required
              type="password"
          />
          <div v-if="errors.password" class="invalid-feedback">
            {{ errors.password[0] }}
          </div>
        </div>

        <button class="btn btn-primary w-100 py-2" type="submit">Login</button>
      </form>

      <div class="text-center mt-2">
        <p>Don't have an account?
          <router-link to="/register">Register here</router-link>
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue';
import axios from 'axios';
import {useRouter} from 'vue-router';
// 导入我们之前创建的 apiClient 实例会更好，但直接用 axios 也可以
// import apiClient from '@/api';

const username = ref('');
const password = ref('');
const errors = ref({}); // 用一个对象来存储所有错误信息
const router = useRouter();

const handleLogin = async () => {
  // 每次提交前，清空之前的错误
  errors.value = {};

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/token/', {
      username: username.value,
      password: password.value,
    });

    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    // 登录成功后，可以重定向到首页或设置全局认证状态
    // 为了看到效果，我们先跳转到首页
    await router.push('/');

  } catch (err) {
    if (err.response && (err.response.status === 400 || err.response.status === 401)) {
      // 将后端返回的错误信息直接赋值给 errors ref
      // Django REST Framework 返回的错误格式正是 { "field_name": ["error message"], ... }
      errors.value = err.response.data;
    } else {
      // 处理网络错误或其他未知错误
      errors.value = {detail: 'An unexpected error occurred. Please try again.'};
    }
    console.error(err);
  }
};
</script>

<style scoped>
/* 我们可以保留一些微调样式，但大部分样式应来自 Bootstrap */
.invalid-feedback {
  /* 确保错误信息总是可见的，因为 Vue 的 v-if 已经控制了它的出现 */
  display: block;
}
</style>
