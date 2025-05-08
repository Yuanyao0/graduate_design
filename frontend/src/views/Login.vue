<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">Login</h2>
      <el-tabs v-model="activeTab" type="card">
        <!-- 账号密码登录 -->
        <el-tab-pane label="账号登录" name="username">
          <el-form @submit.prevent="login" :model="loginForm" >
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="Username" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="loginForm.password"
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
              <el-button type="primary" @click="login" style="width: 100%;">Login</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 邮箱验证码登录 -->
        <el-tab-pane label="邮箱验证码登录" name="email">
          <el-form @submit.prevent="login" :model="emailForm">
            <el-form-item>
              <el-input v-model="emailForm.email" placeholder="Email" :prefix-icon="Message" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="emailForm.code" placeholder="Verification Code" :prefix-icon="Edit">
                <template #append>
                  <el-button
                    type="primary"
                    :disabled="isSending || countdown > 0"
                    @click="sendCode"
                  >
                    {{ countdown > 0 ? `重新发送 (${countdown})` : '发送验证码' }}
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="login" style="width: 100%;">Login</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="register-link">
        <span>Don't have an account?</span>
        <el-link type="primary" @click="goRegister">Register</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../store/user'
import { loginApi, sendCodeApi, emailIfexist } from '../api/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Edit, View, Hide } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 当前使用的登录方式：账号登录 (username) 或 邮箱验证码登录 (email)
const activeTab = ref('username')
const passwordVisible = ref(false)
// 账号密码登录表单
const loginForm = ref({
  username: '',
  password: ''
})

// 邮箱验证码登录表单
const emailForm = ref({
  email: '',
  code: ''
})

// 验证码发送状态与倒计时
const isSending = ref(false)
const countdown = ref(0)
let timer = null

const togglePassword = () => {
  passwordVisible.value = !passwordVisible.value
}
// 开始验证码倒计时
const startCountdown = () => {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

// 发送验证码
const sendCode = async () => {
  if (!emailForm.value.email) {
    ElMessage.warning('请输入邮箱')
    return
  }
  try {
    await emailIfexist(emailForm.value.email)
  }
  catch (err) {
    ElMessage.error(err.response?.data?.message || '邮箱未注册')
    return
  }
  isSending.value = true
  try {
    await sendCodeApi(emailForm.value.email)
    ElMessage.success('验证码已发送')
    startCountdown()
  } catch (err) {
    if (err.response?.status === 429) {
      ElMessage.warning('请勿频繁发送验证码')
    } else {
      ElMessage.error(err.response?.data?.message || '发送失败')
    }
  } finally {
    isSending.value = false
  }
}

// 登录处理，根据 activeTab 判断调用不同接口参数
const login = async () => {
  try {
    if (activeTab.value === 'username') {
      // 账号密码登录
      const res = await loginApi({
        loginways: activeTab.value,
        username: loginForm.value.username,
        password: loginForm.value.password
      })
      // 设置用户信息时，可根据需要调整保存的内容
      userStore.setUser({ username: loginForm.value.username }, res.data.access_token, res.data.refresh_token, res.data.refresh_token_expiry)
    } else if (activeTab.value === 'email') {
      // 邮箱验证码登录，假设后端根据 email 和 code 进行验证
      const res = await loginApi({
        loginways: activeTab.value,
        email: emailForm.value.email,
        code: emailForm.value.code
      })
      // 此处示例采用邮箱作为用户标识，可根据实际业务调整
      userStore.setUser({ username: res.data.username }, res.data.access_token, res.data.refresh_token, res.data.refresh_token_expiry)
    }
    ElMessage.success('Login successful')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || 'Login failed')
  }
}

const goRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f7fa;
}

.login-card {
  width: 400px;
  padding: 40px 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
}

.register-link {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
  font-size: 14px;
}
</style>
