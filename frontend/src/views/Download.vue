<template>
  <div class="download-container">
    <el-card class="query-card">
      <template #header >
        <div class="card-header">
          <span>数据查询条件</span>
          <div>
            <el-button :text="true" @click="goBack" class="back-button">
              <el-icon><ArrowLeft /></el-icon> 返回主界面
            </el-button>
          </div> 
        </div>
      </template>
      
      <el-form :model="queryForm" label-width="120px">
        <!-- 数据集合选择 -->
        <el-form-item label="数据类型">
          <el-radio-group v-model="queryForm.dataType">
            <el-radio-button :value="'observation'">观测数据</el-radio-button>
            <el-radio-button :value="'simulation'">模拟数据</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="数据属性">
          <el-radio-group v-model="queryForm.dataCategory">
            <el-radio-button :value="'hydrology'">水文</el-radio-button>
            <el-radio-button :value="'biomass'">生物</el-radio-button>
            <el-radio-button :value="'environment'">环境</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <!-- 日期范围 -->
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <!-- 经纬度范围 -->
        <el-form-item label="经度范围">
          <el-row :gutter="20">
            <el-col :span="11">
              <el-input v-model.number="queryForm.longitudeMin" placeholder="最小经度" type="number"></el-input>
            </el-col>
            <el-col :span="11">
              <el-input v-model.number="queryForm.longitudeMax" placeholder="最大经度" type="number"></el-input>
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item label="纬度范围">
          <el-row :gutter="20">
            <el-col :span="11">
              <el-input v-model.number="queryForm.latitudeMin" placeholder="最小纬度" type="number"></el-input>
            </el-col>
            <el-col :span="11">
              <el-input v-model.number="queryForm.latitudeMax" placeholder="最大纬度" type="number"></el-input>
            </el-col>
          </el-row>
        </el-form-item>
        
        <!-- 站位查询 -->
        <el-form-item label="站位">
          <el-input v-model="queryForm.location" placeholder="请输入站位"></el-input>
        </el-form-item>
        
        <!-- 水深范围 -->
        <el-form-item label="水深范围(m)">
          <el-row :gutter="20">
            <el-col :span="11">
              <el-input v-model.number="queryForm.waterDeepMin" placeholder="最小水深" type="number"></el-input>
            </el-col>
            <el-col :span="11">
              <el-input v-model.number="queryForm.waterDeepMax" placeholder="最大水深" type="number"></el-input>
            </el-col>
          </el-row>
        </el-form-item>
        
        <!-- 采样层次 -->
        <el-form-item label="采样层次">
          <el-select v-model="queryForm.sampleLevel" placeholder="请选择采样层次" clearable>
            <el-option label="表层(S)" value="S"></el-option>
            <el-option label="底层(B)" value="B"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 水样/网样 -->
        <el-form-item label="水样/网样">
          <el-select v-model="queryForm.waterSampleOrNetSample" placeholder="请选择类型" clearable>
            <el-option label="水样" value="水样"></el-option>
            <el-option label="网样" value="网样"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 采样深度范围 -->
        <el-form-item label="采样深度范围(m)">
          <el-row :gutter="20">
            <el-col :span="11">
              <el-input v-model.number="queryForm.sampleDeepMin" placeholder="最小采样深度" type="number"></el-input>
            </el-col>
            <el-col :span="11">
              <el-input v-model.number="queryForm.sampleDeepMax" placeholder="最大采样深度" type="number"></el-input>
            </el-col>
          </el-row>
        </el-form-item>
        
        <!-- 生物类群 -->
        <el-form-item label="生物类群" v-if="['biomass', ''].includes(queryForm.dataCategory)">
          <el-select v-model="queryForm.group" placeholder="请选择生物类群" clearable>
            <el-option label="硅藻门" value="硅藻门"></el-option>
            <el-option label="甲藻门" value="甲藻门"></el-option>
            <el-option label="甲藻" value="甲藻"></el-option>
            <el-option label="硅藻" value="硅藻"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 底质类型 -->
        <el-form-item label="底质类型">
          <el-select v-model="queryForm.substrateType" placeholder="请选择底质类型" clearable>
            <el-option label="泥" value="泥"></el-option>
            <el-option label="泥沙" value="泥沙"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 采泥器类型 -->
        <el-form-item label="采泥器类型">
          <el-select v-model="queryForm.mudSamplerType" placeholder="请选择采泥器类型" clearable>
            <el-option label="抓斗式" value="抓斗式"></el-option>
            <el-option label="小型抓斗式" value="小型抓斗式"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 采样次数范围 -->
        <el-form-item label="采样次数范围">
          <el-row :gutter="20">
            <el-col :span="11">
              <el-input v-model.number="queryForm.samplingTimesMin" placeholder="最小采样次数" type="number"></el-input>
            </el-col>
            <el-col :span="11">
              <el-input v-model.number="queryForm.samplingTimesMax" placeholder="最大采样次数" type="number"></el-input>
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>
      
      <div class="button-group">
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="success" :disabled="!tableData.length" @click="handleExport">导出</el-button>
      </div>
    </el-card>
    
    <el-card class="result-card" v-if="tableData.length">
      <template #header>
        <div class="card-header">
          <span>查询结果 (共 {{ tableData.length }} 条记录)</span>
        </div>
      </template>
      
      <el-table
        :data="paginatedData"
        border
        style="width: 100%"
        height="500"
        v-loading="loading"
      >
        <el-table-column
          v-for="column in tableColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          min-width="120"
        />
      </el-table>
      
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="tableData.length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import { querydata } from '../api/auth'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()
// 查询表单
const queryForm = ref({
  dataType: '',
  dataCategory: '',
  dateRange: [],
  longitudeMin: null,
  longitudeMax: null,
  latitudeMin: null,
  latitudeMax: null,
  location: '',
  waterDeepMin: null,
  waterDeepMax: null,
  sampleLevel: '',
  waterSampleOrNetSample: '',
  sampleDeepMin: null,
  sampleDeepMax: null,
  group: '',
  substrateType: '',
  mudSamplerType: '',
  samplingTimesMin: null,
  samplingTimesMax: null
})

// 表格数据
const tableData = ref([])
const tableColumns = ref([])
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 计算分页数据
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  // console.log(tableData.value.slice(start, end))
  return tableData.value.slice(start, end)
})

watch(() => queryForm.dataCategory, (newVal) => {
  if (!['biomass', ''].includes(newVal)) {
    queryForm.group = '' // 主动清空
  }
})

// 处理查询
const handleQuery = async () => {
  try {
    loading.value = true
    
    // 构建查询参数
    const params = {
      dataType: queryForm.value.dataType,
      dataCategory: queryForm.value.dataCategory,
      dateRange: queryForm.value.dateRange,
      longitude: {
        min: queryForm.value.longitudeMin,
        max: queryForm.value.longitudeMax
      },
      latitude: {
        min: queryForm.value.latitudeMin,
        max: queryForm.value.latitudeMax
      },
      location: queryForm.value.location,
      waterDeep: {
        min: queryForm.value.waterDeepMin,
        max: queryForm.value.waterDeepMax
      },
      sampleLevel: queryForm.value.sampleLevel,
      waterSampleOrNetSample: queryForm.value.waterSampleOrNetSample,
      sampleDeep: {
        min: queryForm.value.sampleDeepMin,
        max: queryForm.value.sampleDeepMax
      },
      group: queryForm.value.group,
      substrateType: queryForm.value.substrateType,
      mudSamplerType: queryForm.value.mudSamplerType,
      samplingTimes: {
        min: queryForm.value.samplingTimesMin,
        max: queryForm.value.samplingTimesMax
      }
    }
    
    // 发送请求到后端
    const response = await querydata(params)
    
    const data = response.data.results
    console.log(data)
    const colsdict = response.data.colsdict
    // 处理返回数据
    if (data.length > 0) {
      tableData.value = data
      // 动态生成表头
      tableColumns.value = Object.entries(colsdict).map(([key, val]) => ({
        prop: key,
        label: val
      }))
    } else {
      tableData.value = []
      tableColumns.value = []
      ElMessage.info('没有查询到数据')
    }
  } 
  catch (error) {
    ElMessage.error(error.message || '查询失败')
  } 
  finally {
    loading.value = false
  }
}

// 处理重置
const handleReset = () => {
  queryForm.value = {
    dataType: '',
    dataCategory: '',
    dateRange: [],
    longitudeMin: null,
    longitudeMax: null,
    latitudeMin: null,
    latitudeMax: null,
    location: '',
    waterDeepMin: null,
    waterDeepMax: null,
    sampleLevel: '',
    waterSampleOrNetSample: '',
    sampleDeepMin: null,
    sampleDeepMax: null,
    group: '',
    substrateType: '',
    mudSamplerType: '',
    samplingTimesMin: null,
    samplingTimesMax: null
  }
  tableData.value = []
  tableColumns.value = []
  currentPage.value = 1
}

// 处理导出
const handleExport = async () => {
  try {
    ElMessageBox.confirm('请选择导出格式', '导出数据', {
      distinguishCancelAndClose: true,
      confirmButtonText: 'Excel',
      cancelButtonText: 'CSV'
    })
    .then(() => {
      exportToExcel()
    })
    .catch(action => {
      if (action === 'cancel') {
        exportToCSV()
      }
    })
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

// 导出为Excel
// const exportToExcel = () => {
//   try {
//     // 字段映射：prop -> label
//     const fieldMap = tableColumns.value.reduce((map, col) => {
//       map[col.prop] = col.label
//       return map
//     }, {})

//     // 构造用于导出的数据，key 为 label，值为原始值
//     const formattedData = tableData.value.map(row => {
//       const newRow = {}
//       for (const prop in fieldMap) {
//         newRow[fieldMap[prop]] = row[prop]
//       }
//       return newRow
//     })

//     // 创建工作表
//     const ws = XLSX.utils.json_to_sheet(formattedData)
//     // 创建工作簿
//     const wb = XLSX.utils.book_new()
//     XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
//     // 导出文件
//     XLSX.writeFile(wb, 'data_export.xlsx')
//     ElMessage.success('Excel导出成功')
//   } catch (error) {
//     ElMessage.error('Excel导出失败: ' + error.message)
//   }
// }

const exportToExcel = () => {
  try {
    // 字段映射：prop -> label
    const fieldMap = tableColumns.value.reduce((map, col) => {
      map[col.prop] = col.label
      return map
    }, {})

    const props = Object.keys(fieldMap)
    const headers = props.map(prop => fieldMap[prop])

    // 构造二维数组，第一行为标题，后面为数据行（值按字段顺序排列）
    const data = [
      headers, // 第一行：表头（label）
      ...tableData.value.map(row => props.map(prop => row[prop])) // 后续行：数据值
    ]

    // 创建工作表
    const ws = XLSX.utils.aoa_to_sheet(data)
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
    // 导出文件
    XLSX.writeFile(wb, 'data_export.xlsx')
    ElMessage.success('Excel导出成功')
  } catch (error) {
    ElMessage.error('Excel导出失败: ' + error.message)
  }
}

// 导出为CSV
const exportToCSV = () => {
  try {
    // 获取所有label
    const fields = tableColumns.value.map(col => col.label)
    
    // 创建CSV内容
    let csvContent = fields.join(',') + '\n'
    
    tableData.value.forEach(row => {
      const rowValues = fields.map(field => {
        // 查找prop对应的值
        const prop = tableColumns.value.find(col => col.label === field)?.prop
        const value = row[prop]
        return value === undefined || value === null ? 'NaN' : `"${value}"`
      })
      csvContent += rowValues.join(',') + '\n'
    })
    
    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'data_export.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('CSV导出成功')
  } catch (error) {
    ElMessage.error('CSV导出失败: ' + error.message)
  }
}


// 分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

// 当前页变化
const handleCurrentChange = (val) => {
  currentPage.value = val
}
 
const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
.back-button {
  font-size: 16px;
}

.download-container {
  padding: 20px;
}

.query-card, .result-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 20px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.button-group {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  gap: 20px;
}

.el-form-item {
  margin-bottom: 18px;
}

.el-pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>