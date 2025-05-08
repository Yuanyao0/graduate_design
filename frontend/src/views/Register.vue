<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">Register</h2>
      <el-form @submit.prevent="register" :model="{ username, email, password, code }">
        <el-form-item>
          <el-input v-model="username" placeholder="Username" :prefix-icon="User" />
        </el-form-item>

        <el-form-item>
          <el-input v-model="email" placeholder="Email" :prefix-icon="Message" />
        </el-form-item>

        <el-form-item>
          <el-row style="width: 100%;" :gutter="10">
            <el-col :span="16">
              <el-input v-model="code" placeholder="Verification Code" :prefix-icon="Edit" />
            </el-col>
            <el-col :span="8">
              <el-button :disabled="countdown > 0" @click="sendCode" type="primary" style="width: 100%;">
                {{ countdown > 0 ? countdown + 's' : 'Send Code' }}
              </el-button>
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="password"
            :type="passwordVisible ? 'text' : 'password'"
            placeholder="Password"
            :prefix-icon="Lock" 
          >
            <template #suffix>
              <el-icon :style="{ cursor: 'pointer' }" @click="togglePassword">
                <View v-if="!passwordVisible" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="register" style="width: 100%;">Register</el-button>
        </el-form-item>

        <div class="login-link">
          <span>Already have an account?</span>
          <el-link type="primary" @click="goLogin">Login</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { registerApi, sendCodeApi } from '../api/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Edit, View, Hide } from '@element-plus/icons-vue'

const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const passwordVisible = ref(false)
const countdown = ref(0)
let timer = null

const router = useRouter()

const sendCode = async () => {
  if (!email.value || !/^[\w.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email.value)) {
    ElMessage.warning('Please enter a valid email.')
    return
  }
  try {
    await sendCodeApi(email.value)
    ElMessage.success('Verification code sent.')
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (err) {
    if (err.response?.status === 429) {
      ElMessage.warning('请勿频繁发送验证码')
    }
    else {
      ElMessage.error(err.response?.data?.message || 'Failed to send code')
    }
  }
}

const register = async () => {
  if (!username.value || !email.value || !password.value || !code.value) {
    ElMessage.warning('Please complete all fields.')
    return
  }
  try {
    await registerApi({
      username: username.value,
      email: email.value,
      password: password.value,
      code: code.value
    })
    ElMessage.success('Register Success! Please login.')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || 'Register failed')
  }
}

const togglePassword = () => {
  passwordVisible.value = !passwordVisible.value
}

const goLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}

.register-card {
  width: 400px;
  padding: 40px 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.register-title {
  text-align: center;
  margin-bottom: 30px;
}

.login-link {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
  font-size: 14px;
}
</style>
