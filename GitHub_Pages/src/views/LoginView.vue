<template>
  <div class="login-container">
    <form @submit.prevent="handleLogin">
      <h1>Login</h1>
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" v-model="username" id="username" required/>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" v-model="password" id="password" required/>
      </div>
      <p v-if="error" class="error-message">{{ error }}</p>
      <button type="submit">Login</button>
    </form>
  </div>
</template>

<script setup>
import {ref} from 'vue';
import axios from 'axios';
import {useRouter} from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const handleLogin = async () => {
  try {
    // 向 Django 后端发送登录请求
    const response = await axios.post('http://127.0.0.1:8000/api/token/', {
      username: username.value,
      password: password.value,
    });

    // 登录成功
    console.log(response.data);
    error.value = '';

    // 将 tokens 保存到 localStorage
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    // 跳转到主页或仪表盘页面
    router.push('/'); // 或者你想要跳转的任何受保护页面

  } catch (err) {
    // 登录失败
    if (err.response && err.response.status === 401) {
      error.value = '用户名或密码错误。';
    } else {
      error.value = '发生未知错误，请稍后再试。';
    }
    console.error(err);
  }
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

.error-message {
  color: red;
}
</style>
