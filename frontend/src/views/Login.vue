<template>
  <div>
    <h2>Login</h2>
    <form @submit.prevent="login">
      <input v-model="username" placeholder="Username" />
      <input v-model="password" type="password" placeholder="Password" />
      <button type="submit">Login</button>
    </form>
    <p @click="goRegister" style="cursor: pointer; color: blue;">Don't have an account? Register</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../store/user'
import { loginApi } from '../api/auth'
import { useRouter } from 'vue-router'


// ref 和 reactive, 值用 ref，结构用 reactive；取 ref 要 .value，reactive 直接拿
const router = useRouter()
const username = ref('')
const password = ref('')
const userStore = useUserStore()

const login = async () => {
  try {
    // Axios Response 对象
    // {
    // data: {},          // 服务器返回的真正数据（最常用）
    // status: 200,       // HTTP 状态码，比如200，404，500
    // statusText: 'OK',  // 状态文本，比如"OK"
    // headers: {},       // 返回头信息
    // config: {},        // 本次请求的配置信息
    // request: {}        // 请求本身的信息（一般很少用）
    // }
    const res = await loginApi({
      username: username.value,
      password: password.value
    })
    // console.log('login res:', res)  
    const access_token = res.data.access_token
    const refresh_token = res.data.refresh_token
    const refresh_token_expiry = res.data.refresh_token_expiry
    userStore.setUser({ username: username.value }, access_token, refresh_token, refresh_token_expiry)
    router.push('/')
  } catch (error) {
    console.error('Login error:', error)
    alert(error.response?.data?.message || 'Login failed')
  }
}

const goRegister = () => {
  router.push('/register')
}

</script>
