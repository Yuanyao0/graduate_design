<template>
  <div>
    <h2>Home Page</h2>
    <p>Welcome, {{ user?.username }}</p>
    <button @click="logout">Logout</button>
    <div>
      <el-upload
        class="upload-area"
        drag
        action="http://localhost:5000/api/upload"
        :limit="1"
        :show-file-list="false"
        :on-success="handleSuccess"
        :on-error="handleError"
        :before-upload="beforeUpload"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">拖拽文件到此或点击上传</div>
      </el-upload>
    </div>
    <div>
      <el-dialog
        v-model="dialogVisible"
        title="导入数据（导入数据库将以英文字段名导入）"
        width="60%"
        :close-on-click-modal="false"
      >
        <el-table :data="selectedFields" style="margin-bottom: 20px">
          <el-table-column prop="oldName" label="原字段名" />
          <el-table-column label="英文名">
            <template #default="scope">
              <el-input v-model="scope.row.newName" />
            </template>
          </el-table-column>
          <el-table-column label="导入">
            <template #default="scope">
              <el-checkbox v-model="scope.row.enabled" />
            </template>
          </el-table-column>
        </el-table>

        <el-form label-width="80px" style="margin-bottom: 20px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数据来源">
                <el-select v-model="dataType" placeholder="请选择数据类型" style="width: 100%">
                  <el-option label="观测数据" value="observation" />
                  <el-option label="模拟数据" value="simulation" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="数据属性">
                <el-select v-model="dataAttr" placeholder="请选择数据属性" style="width: 100%">
                  <el-option label="水文" value="hydrology" />
                  <el-option label="生物" value="biomass" />
                  <el-option label="环境" value="environment" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <template #footer>
          <el-button type="primary" @click="submitImport">提交导入</el-button>
          <el-button type="primary" @click="cancelImport">取消导入</el-button>
        </template>
      </el-dialog>
      <el-button type="primary" @click="goToDownloadPage">下载文件</el-button>
    </div>
  </div>

</template>

<script setup>
import { useUserStore } from '../store/user'
import { ref } from 'vue'
import { importApi, cancelImportApi } from '../api/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'


const userStore = useUserStore()
const router = useRouter()
const user = userStore.user
const dialogVisible = ref(false)
const fields = ref([])
const selectedFields = ref([])
const uploadedFile = ref('')
const dataType = ref('')
const dataAttr = ref('')


const reset = () => {
  fields.value = []
  selectedFields.value = []
  uploadedFile.value = ''
  dataType.value = ''
  dataAttr.value = ''
  dialogVisible.value = false
}

const handleSuccess = (res, file) => {
  uploadedFile.value = file.name
  fields.value = res.fields
  selectedFields.value = fields.value.map(name => ({
    oldName: name,
    newName: "",
    enabled: true,
  }))
  dialogVisible.value = true
}

const handleError = (err, file) => {
  try {
    const responseText = err?.target?.responseText
    const json = JSON.parse(responseText)
    if (json.error) {
      ElMessage.error(`上传失败：${json.error}`)
    } else {
      ElMessage.error('上传失败：服务器返回未知错误')
    }
  } catch {
    ElMessage.error('上传失败：无法解析错误信息')
  }
}

const beforeUpload = (file) => {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  return true
}

const submitImport = async () => {
  const enabledIndices = selectedFields.value
  .map((f, index) => (f.enabled ? index : -1))
  .filter(index => index !== -1);
  const config = {
    filename: uploadedFile.value,
    fields: selectedFields.value.filter(f => f.enabled),
    enabledIndices: enabledIndices,
    dataType: dataType.value,
    dataAttr: dataAttr.value

  }
  const res = await importApi(config)
  if (res.status == 401) ElMessage.info('取消操作已中止')
  ElMessage.success('导入成功')
  reset()
}

const cancelImport = async () => {
  try {
    await ElMessageBox.confirm('确定取消导入吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await cancelImportApi({filename: uploadedFile.value})
    ElMessage.success('文件已取消导入')
    reset()
  } catch {
    // ElMessage.info('取消操作已中止')
  }
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}

const goToDownloadPage = () =>{
  router.push('/download')
}
</script>

<style scoped>
.upload-area {
  border: 2px dashed #dcdfe6;
  padding: 40px;
  text-align: center;
  margin-bottom: 30px;
  border-radius: 8px;
  background-color: #f9f9f9;
  transition: border-color 0.3s;
}
.upload-area:hover {
  border-color: #409eff;
}
</style>

