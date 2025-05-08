<template>
  <div class="user-info-container">
    <div class="back-button-container">
      <el-button type="text" @click="goBack" class="back-button">
        <el-icon><ArrowLeft /></el-icon> 返回主界面
      </el-button>
    </div>    
    <el-card>
      <h3>账户信息</h3>

      <!-- 用户名 -->
      <div class="info-item">
        <span>用户名：{{ user.username }}</span>
        <el-button text @click="editField('username')">修改</el-button>
      </div>
      <div v-if="editingField === 'username'" style="display: flex; align-items: center; gap: 8px;">
        <el-input
          v-model="form.username"
          style="flex: 1;"
        />
        <el-button  type = 'primary' @click="saveField('username')">提交</el-button>
      </div>

      <!-- 密码（直接修改） -->
      <div class="info-item">
        <span>密码：******</span>
        <el-button text @click="editField('password')">修改</el-button>
      </div>
      <div v-if="editingField === 'password'" style="display: flex; align-items: center; gap: 8px;">
        <el-input
          v-model="form.password"
          :type="passwordVisible ? 'text' : 'password'"
          placeholder="请输入新密码"
          style="flex: 1;"
        >
          <template #suffix>
            <el-icon :style="{ cursor: 'pointer' }" @click="togglePassword">
              <View v-if="!passwordVisible" />
              <Hide v-else />
            </el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="saveField('password')">提交</el-button>
      </div>
      <!-- 邮箱 -->
      <div class="info-item">
        <span>邮箱：{{ user.email }}</span>
        <el-button text @click="editField('email')">修改</el-button>
      </div>
      <div v-if="editingField === 'email'">
        <el-input v-model="form.email" placeholder="新邮箱" />
        <el-input v-model="form.code" placeholder="验证码" />
        <el-button size="small" @click="sendCode" :disabled="countdown > 0">
          {{ countdown > 0 ? `${countdown}s后重试` : '发送验证码' }}
        </el-button>
        <el-button type="primary" @click="saveField('email')">确认修改</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserInfoApi, sendCodeApi, updateUserInfoApi, emailIfexist } from '../api/auth'
import { useRouter } from 'vue-router'
import { View, Hide, ArrowLeft } from '@element-plus/icons-vue'

const user = ref({ username: '', email: ''})
const router = useRouter()
const form = ref({ username: '', password: '', email: '', code: '' })
const editingField = ref('')
const countdown = ref(0)
const passwordVisible = ref(false)
let timer = null

onMounted(async () => {
  const res = await getUserInfoApi()
  user.value = res.data
})

const editField = (field) => {
  editingField.value = field
  form.value[field] = user.value?.[field] ?? ''
}

const togglePassword = () => {
  passwordVisible.value = !passwordVisible.value
}

const saveField = async (field) => {
  if (field === 'email') {
    if (!form.value.code) {
      ElMessage.warning('请输入验证码')
      return
    }
  }
  try{
    await updateUserInfoApi({ category: field, [field]: form.value[field], code: form.value.code })
    ElMessage.success('修改成功')
    user.value[field] = form.value[field]
    editingField.value = ''
  }
  catch (err){
    ElMessage.error(err.response?.data?.message || '修改失败')
  }
}

const sendCode = async () => {
  const res = await emailIfexist( form.value.email )
  if (res.status==200){
    ElMessage.error('邮箱已经存在')
    return
  }
  await sendCodeApi( form.value.email ) 
  ElMessage.success('验证码已发送')
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}
const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
.back-button-container {
  margin-bottom: 20px;
}
.back-button {
  font-size: 14px;
  color: #409EFF;
  display: flex;
  align-items: center;
}

.user-info-container {
  max-width: 600px;
  margin: 40px auto;
}
.info-item {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
}
</style>

