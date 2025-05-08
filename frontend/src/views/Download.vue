<template>
  <div>
    <div class="header-bar">
      <h3>文件下载页面</h3>
      <el-button type="text" @click="goBack" class="back-button">
        <el-icon><ArrowLeft /></el-icon> 返回主界面
      </el-button>
    </div>
    <!-- 筛选条件 -->
    <el-form label-width="80px" class="mb-4">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filters.date"
              type="daterange"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 100%"
              clearable
              @change="handleDateChange"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="类型">
            <el-select v-model="filters.fileType" placeholder="选择文件类型" style="width: 100%">
              <el-option label="观测数据" value="observation" />
              <el-option label="模拟数据" value="simulation" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="属性">
            <el-select v-model="filters.dataAttr" placeholder="选择文件属性" style="width: 100%">
              <el-option label="水文" value="hydrology" />
              <el-option label="生物" value="biomass" />
              <el-option label="环境" value="environment" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    
    <el-row :gutter="20" class="mb-4">
      <el-col :span="20">
        <el-input v-model="filters.search" placeholder="搜索文件名..." />
      </el-col>
      <el-col :span="4">
        <el-button type="default" @click="resetFilters" style="width: 100%">重置筛选</el-button>
      </el-col>
    </el-row>

    <!-- 文件表格 -->
    <!-- <el-table :data="pagedFiles" stripe>
      <el-table-column prop="filename" label="文件名" />
      <el-table-column prop="filesize" label="大小" />
      <el-table-column prop="upload_time" label="上传时间" />
      <el-table-column prop="download_times" label="下载次数" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="small" @click="handleDownload(scope.row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table> -->
    <el-table :data="pagedFiles" stripe @selection-change="handleSelectionChange" ref="fileTable">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="filename" label="文件名" />
      <el-table-column prop="filesize" label="大小" />
      <el-table-column prop="upload_time" label="上传时间" />
      <el-table-column prop="download_times" label="下载次数" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="small" @click="handleDownload(scope.row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="downloadDialogVisible" title="选择下载格式" width="30%">
      <el-form>
        <el-form-item label="格式">
          <el-select v-model="selectedFormat" placeholder="请选择格式">
            <el-option label="CSV" value="csv" />
            <el-option label="Excel" value="excel" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="downloadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDownload">下载</el-button>
        </span>
      </template>
    </el-dialog>
    <el-button type="primary" class="mb-4" :disabled="!multipleSelection.length" @click="openBatchDownloadDialog">
      批量下载
    </el-button>
    <el-dialog v-model="batchDownloadDialogVisible" title="选择批量下载格式" width="30%">
      <el-form>
        <el-form-item label="格式">
          <el-select v-model="batchFormat" placeholder="请选择格式">
            <el-option label="CSV" value="csv" />
            <el-option label="Excel" value="excel" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchDownloadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBatchDownload">下载</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分页 -->
    <el-pagination
      class="mt-4"
      layout="prev, pager, next"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="filteredFiles.length"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getfileInfo, downloadFile, downloadBatchFiles } from '../api/auth'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const files = ref([])
const currentPage = ref(1)
const pageSize = 10
const downloadDialogVisible = ref(false)
const selectedFormat = ref('')
const selectedFile = ref(null)
const multipleSelection = ref([]);
const batchFormat = ref('');
const batchDownloadDialogVisible = ref(false);

const filters = ref({
  date: [],
  fileType: '',
  dataAttr: '',
  search: ''
})


// 获取文件数据
const fetchFiles = async () => {
  try {
    const res = await getfileInfo()
    files.value = res.data.files;
  } catch (err) {
    console.error('获取文件失败:', err);
  }
};


onMounted(fetchFiles)


const handleSelectionChange = (val) => {
  multipleSelection.value = val
}

const openBatchDownloadDialog = () => {
  batchFormat.value = ''
  batchDownloadDialogVisible.value = true
}

const handleDateChange = (val) => {
  if (!val || val.length === 0) {
    filters.value.date = []
  }
}


// 过滤后的文件
const filteredFiles = computed(() => {
  return files.value.filter(file => {
    if (filters.value.search && !(file.filename || '').toLowerCase().includes(filters.value.search.toLowerCase())) return false
    if (filters.value.fileType && file.datatype !== filters.value.fileType) return false
    if (filters.value.dataAttr && file.dataattr !== filters.value.dataAttr) return false
    if (
      filters.value.date.length === 2 &&
      (new Date(file.upload_time) < new Date(filters.value.date[0]) ||
        new Date(file.upload_time) > new Date(filters.value.date[1]))
    ) {
      return false;
    }
    return true;
  });
});

watch(filteredFiles, () => {
  if ((currentPage.value - 1) * pageSize >= filteredFiles.value.length) {
    currentPage.value = 1
  }
})

// 当前分页展示数据
const pagedFiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredFiles.value.slice(start, start + pageSize);
})

const handlePageChange = (page) => {
  currentPage.value = page
}

const resetFilters = () => {
  filters.value = {
    date: [],
    fileType: '',
    dataAttr: '',
    search: ''
  }
  currentPage.value = 1
}

// 下载文件
const handleDownload = (file) => {
  selectedFile.value = file
  selectedFormat.value = ''
  downloadDialogVisible.value = true
}

const confirmDownload = async () => {
  const format = selectedFormat.value
  if (!format || !selectedFile.value) return
  const data = {
      params: { format },
      responseType: 'blob'
  }
  try {
    const res = await downloadFile(selectedFile.value.id, data)
    const blob = new Blob([res.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    const originalName = selectedFile.value.filename;
    const baseName = originalName.replace(/\.[^/.]+$/, '');  // 去掉最后一个 .xxx 后缀
    const ext = format === 'excel' ? 'xlsx' : 'csv';
    link.download = `${baseName}.${ext}`;
    link.click()
    URL.revokeObjectURL(link.href)
    const updatedCount = parseInt(res.headers['x-download-times'])
    console.log(res)
    if (!isNaN(updatedCount)) {
      const target = files.value.find(f => f.id === selectedFile.value.id)
      if (target) {
        target.download_times = updatedCount
      }
    }
    downloadDialogVisible.value = false

  } catch (err) {
    console.error('下载失败:', err)
  }
}


// 批量下载
const confirmBatchDownload = async () => {
  if (!batchFormat.value || multipleSelection.value.length === 0) return;

  const ids = multipleSelection.value.map(f => f.id);
  try {
    const res = await downloadBatchFiles(ids, batchFormat.value); 
    const blob = new Blob([res.data]);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `download_batch_${Date.now()}.zip`;
    link.click();
    URL.revokeObjectURL(link.href);
    batchDownloadDialogVisible.value = false;
  } catch (err) {
    console.error('批量下载失败:', err);
  }
};

const goBack = () => {
  router.push('/') 
}
</script>

<style scoped>
.mb-4 {
  margin-bottom: 20px;
}
.mt-4 {
  margin-top: 20px;
}
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.back-button {
  font-size: 14px;
  color: #409EFF;
}
</style>
