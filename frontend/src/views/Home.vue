<template>
  <div class="container">
    <!-- 顶部导航栏 -->
    <div class="header">
      <h2>海洋大数据管理系统</h2>
      <div class="user-info">
        <el-dropdown>
          <span class="el-dropdown-link">
            <el-avatar :size="32" :style="{backgroundColor: '#409EFF', color: '#fff'}">
              {{ user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="username">{{ user?.username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToUserInfo">个人信息</el-dropdown-item>
              <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 欢迎语 -->
    <p class="welcome-text">欢迎回来，{{ user?.username }}!</p>

    <!-- 操作区域 -->
    <div class="action-area">
      <!-- 上传区域 -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-card"
          drag
          action="http://localhost:5000/api/upload"
          :limit="1"
          :show-file-list="false"
          :on-success="handleSuccess"
          :on-error="handleError"
          :before-upload="beforeUpload"
        >
          <i class="el-icon-upload"></i>
          <div class="el-upload__text">拖拽文件到此处<br>或点击上传</div>
        </el-upload>
      </div>

      <!-- 下载按钮 -->
      <div class="download-section">
        <el-button 
          type="primary" 
          class="download-btn" 
          @click="goToDownloadPage"
        >
          <i class="el-icon-download"></i>
          <span>下载文件</span>
        </el-button>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <el-divider content-position="left">文件列表</el-divider>
      <el-table 
        :data="fileList" 
        stripe 
        v-loading="loading"
        height="calc(100vh - 380px)"
      >
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="username" label="上传用户" />
        <el-table-column prop="filesize" label="大小(KB)" />
        <el-table-column prop="upload_time" label="上传时间" />
        <el-table-column prop="datatype" label="数据类型" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="small" @click="deleteFile(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="perPage"
          :total="total"
          @current-change="handlePageChange"
          layout="prev, pager, next, jumper"
          background
        />
      </div>
    </div>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="导入数据配置"
      width="60%"
      :close-on-click-modal="false"
    >
      <!-- 对话框内容保持不变 -->
      <!-- ... -->
    </el-dialog>
  </div>
</template>

<script setup>
import { useUserStore } from '../store/user'
import { ref, onMounted } from 'vue'
import { importApi, cancelImportApi, fetchAttrSuggestions, checkEngnameExist, getfileInfo, checkfilename, deletefile } from '../api/auth'
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
const uploadRef = ref(null)
const attrSuggestions = ref({}) 
const fileList = ref([])
const loading = ref(false)
const currentPage = ref(1)  // 当前页
const perPage = ref(10)  // 每页显示的文件数
const total = ref(0)  // 总记录数

const reset = () => {
  fields.value = []
  selectedFields.value = []
  uploadedFile.value = ''
  dataType.value = ''
  dataAttr.value = ''
  dialogVisible.value = false
  attrSuggestions.value = {}
  uploadRef.value?.clearFiles()  // 清空上传状态
}

const fetchFiles = async () => {
  loading.value = true
  const params = {
    page: currentPage.value,
    per_page: perPage.value
  }
  const res = await getfileInfo(params)
  fileList.value = res.data.files
  total.value = res.data.total
  loading.value = false
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchFiles()  // 切换页码时重新加载数据
}

onMounted(fetchFiles)

const handleSuccess = async (res, file) => {
  uploadedFile.value = file.name
  fields.value = res.fields
  const resdata = await fetchAttrSuggestions(res.fields)
  attrSuggestions.value = resdata.data
  selectedFields.value = fields.value.map(name => ({
    colname: name,
    selectedAttr: attrSuggestions.value[name][0] || null, // 默认选择最匹配的
    customEngName: '',
    customDataType: '',
    enabled: true,
    satisfied: !!attrSuggestions.value[name].length
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

const beforeUpload = async (file) => {
  const allowedTypes = [
    'text/csv',
    'text/plain',                // .txt
    'application/vnd.ms-excel', // .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' // .xlsx
  ]
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持上传 CSV、TXT 或 Excel 文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  const res = await checkfilename(file.filename)
  if (res.data.exists) {
    try {
      await ElMessageBox.confirm('已有同名文件，是否仍要导入？', '提示', {
        confirmButtonText: '继续导入',
        cancelButtonText: '取消',
        type: 'warning',
      })
      return true
    } catch {
      return false
    }
  }
  return true
}

// const submitImport = async () => {
//   const enabledIndices = selectedFields.value
//   .map((f, index) => (f.enabled ? index : -1))
//   .filter(index => index !== -1);
//   const config = {
//     filename: uploadedFile.value,
//     fields: selectedFields.value.filter(f => f.enabled),
//     enabledIndices: enabledIndices,
//     dataType: dataType.value,
//     dataAttr: dataAttr.value
//   }
//   const res = await importApi(config)
//   if (res.status == 401) ElMessage.info('取消操作已中止')
//   ElMessage.success('导入成功')
//   reset()
// }

const onInputEngName = async (engName) => {
  try{
    await checkEngnameExist(engName)
  }
  catch (err){
    ElMessage.error(err.response?.data?.error || '英文名有误')
  }
}

const submitImport = async () => {
  const fieldConfigs = selectedFields.value.filter(f => f.enabled).map(f => {
    const usingCustom = !f.selectedAttr || f.selectedAttr === 'custom'

    return {
      colname: f.colname,
      attrname: f.selectedAttr,
      engName: usingCustom ? f.customEngName : '',
      datatype: usingCustom ? f.customDataType : '',
      newAttr: usingCustom,  // 是否是新增属性
    }
  })

  const config = {
    filename: uploadedFile.value,
    fields: fieldConfigs,
    dataType: dataType.value,
    dataAttr: dataAttr.value
  }

  await importApi(config)
  ElMessage.success('导入成功')
  fetchFiles()
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

const deleteFile = async (fileobj) => {
  try {
    const res = await deletefile(fileobj.fileid)
    ElMessage.success(res.data.message)
    fetchFiles()
  }
  catch (err) {
    ElMessage.error(err.response?.data?.message||'文件删除失败')
  }
}
const goToUserInfo = () => {
  router.push('/userinfo')
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}

const goToDownloadPage = () => {
  router.push('/download')
}
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 顶部导航栏 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  color: #303133;
  font-size: 24px;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 8px;
  font-weight: 500;
  color: #606266;
}

/* 欢迎语 */
.welcome-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 20px;
}

/* 操作区域 */
.action-area {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.upload-section {
  flex: 1;
}

.download-section {
  width: 150px;
}

/* 上传卡片 */
.upload-card {
  border: 1px dashed #DCDFE6;
  border-radius: 8px;
  padding: 20px;
  background-color: #F5F7FA;
  transition: all 0.3s;
  height: 76%;
}

.upload-card:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-upload-dragger {
  width: 100%;
  padding: 20px;
  background: transparent;
  border: none;
}

.el-icon-upload {
  font-size: 40px;
  color: #409EFF;
  margin-bottom: 10px;
}

.el-upload__text {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

/* 下载按钮 */
.download-btn {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.download-btn i {
  font-size: 32px;
  margin-bottom: 8px;
}

.download-btn span {
  font-size: 20px;
}

/* 文件列表 */
.file-list {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-divider {
  margin: 0 0 20px 0;
}

/* 分页 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>