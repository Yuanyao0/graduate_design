<template>
  <div class="register">
    <h2>Register</h2>
    <form @submit.prevent="register">
      <input v-model="username" placeholder="Username" />
      <input v-model="password" type="password" placeholder="Password" />
      <button type="submit">Register</button>
    </form>
    <p @click="goLogin" style="cursor: pointer; color: blue;">Already have an account? Login</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { registerApi } from '../api/auth'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const router = useRouter()

const register = async () => {
  try {
    await registerApi({ username: username.value, password: password.value })
    alert('Register Success! Please Login.')
    router.push('/login')
  } catch (error) {
    alert(error.response.data.message || 'Register failed')
  }
}

const goLogin = () => {
  router.push('/login')
}
</script>
