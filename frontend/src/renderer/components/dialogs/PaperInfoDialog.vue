<template>
  <el-dialog
    v-model="visible"
    title="📊 论文版面详细信息"
    width="600px"
    :close-on-click-modal="false"
    class="paper-info-dialog"
  >
    <div v-loading="loading" class="dialog-content">
      <!-- 加载失败提示 -->
      <el-alert
        v-if="error"
        type="error"
        :title="error"
        :closable="false"
        show-icon
      />
      
      <!-- 元数据内容 -->
      <div v-else-if="metadata" class="metadata-content">
        <!-- PDF名称 -->
        <div class="info-section">
          <div class="section-header">
            <el-icon><DocumentCopy /></el-icon>
            <span>PDF名称</span>
          </div>
          <div class="section-content">
            <el-text class="pdf-name-text">{{ metadata.pdf_name }}</el-text>
          </div>
        </div>

        <!-- 强段落宽度 -->
        <div v-if="paperLayout" class="info-section">
          <div class="section-header">
            <el-icon><DocumentChecked /></el-icon>
            <span>强段落信息</span>
          </div>
          <div class="section-content">
            <el-descriptions :column="1" border size="default">
              <el-descriptions-item label="平均宽度">
                <el-tag type="success" size="large">{{ paperLayout.strong_paragraph_width }} px</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="元素数量">
                <el-tag size="large">{{ paperLayout.strong_paragraph_count }} 个</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 栏数布局 -->
        <div v-if="paperLayout" class="info-section">
          <div class="section-header">
            <el-icon><Grid /></el-icon>
            <span>栏数布局</span>
          </div>
          <div class="section-content">
            <el-descriptions :column="1" border size="default">
              <el-descriptions-item label="布局类型">
                <el-tag :type="getLayoutTagType(paperLayout.layout_type)" size="large">
                  {{ getLayoutTypeName(paperLayout.layout_type) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="栏数">
                <el-tag type="info" size="large">{{ paperLayout.column_count }} 栏</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 栏位置信息 -->
        <div v-if="paperLayout && paperLayout.column_positions" class="info-section">
          <div class="section-header">
            <el-icon><Location /></el-icon>
            <span>栏位置信息</span>
          </div>
          <div class="section-content">
            <el-table 
              :data="paperLayout.column_positions" 
              border 
              size="default"
              :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
            >
              <el-table-column type="index" label="序号" width="80" align="center" />
              <el-table-column label="X 坐标" align="center">
                <template #default="{ row }">
                  <el-tag>{{ row.x.toFixed(2) }} px</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="样本数量" align="center">
                <template #default="{ row }">
                  <el-tag type="success">{{ row.sample_count }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 版本信息 -->
        <div class="info-section">
          <div class="section-header">
            <el-icon><InfoFilled /></el-icon>
            <span>元数据版本</span>
          </div>
          <div class="section-content">
            <el-tag type="info">{{ metadata.version }}</el-tag>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty 
        v-else 
        description="暂无论文版面分析数据"
        :image-size="100"
      />
    </div>

    <template #footer>
      <el-button @click="closeDialog">关闭</el-button>
      <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { 
  DocumentCopy, 
  DocumentChecked, 
  Grid, 
  Location, 
  InfoFilled,
  Refresh
} from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  pdfName: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const error = ref('')
const metadata = ref(null)

// 计算属性
const paperLayout = ref(null)

// 监听对话框显示状态
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadMetadata()
  }
})

watch(visible, (newVal) => {
  if (!newVal) {
    emit('update:modelValue', false)
  }
})

// 加载元数据
const loadMetadata = async () => {
  if (!props.pdfName) {
    error.value = 'PDF名称不能为空'
    return
  }

  loading.value = true
  error.value = ''
  metadata.value = null
  paperLayout.value = null

  try {
    const response = await axios.get(
      `http://127.0.0.1:8000/api/v1/annotation/${encodeURIComponent(props.pdfName)}/metadata`
    )

    if (response.data.code === 200) {
      metadata.value = response.data.data
      paperLayout.value = response.data.data.paper_layout
    } else {
      error.value = response.data.message || '加载失败'
    }
  } catch (err) {
    console.error('加载论文版面数据失败:', err)
    error.value = err.response?.data?.detail || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadMetadata()
  window.$toast?.success('数据已刷新')
}

// 关闭对话框
const closeDialog = () => {
  visible.value = false
}

// 获取布局类型名称
const getLayoutTypeName = (type) => {
  const typeMap = {
    'single_column': '单栏布局',
    'double_column': '双栏布局',
    'triple_column': '三栏布局'
  }
  return typeMap[type] || type
}

// 获取布局类型标签颜色
const getLayoutTagType = (type) => {
  const tagTypeMap = {
    'single_column': 'success',
    'double_column': 'warning',
    'triple_column': 'danger'
  }
  return tagTypeMap[type] || 'info'
}
</script>

<style scoped lang="scss">
.paper-info-dialog {
  :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    margin: 0;
    
    .el-dialog__title {
      color: white;
      font-size: 18px;
      font-weight: 600;
    }
    
    .el-dialog__close {
      color: white;
      
      &:hover {
        color: #f0f0f0;
      }
    }
  }

  :deep(.el-dialog__body) {
    padding: 20px;
    max-height: 600px;
    overflow-y: auto;
  }

  :deep(.el-dialog__footer) {
    padding: 15px 20px;
    border-top: 1px solid #e4e7ed;
    background-color: #f5f7fa;
  }
}

.dialog-content {
  min-height: 200px;
}

.metadata-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-section {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    border-bottom: 1px solid #e4e7ed;
    font-weight: 600;
    color: #333;
    
    .el-icon {
      font-size: 18px;
      color: #667eea;
    }
  }
  
  .section-content {
    padding: 16px;
  }
}

.pdf-name-text {
  font-size: 14px;
  color: #606266;
  word-break: break-all;
}

:deep(.el-descriptions__body) {
  background: white;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-tag) {
  font-weight: 500;
}

:deep(.el-empty) {
  padding: 40px 0;
}
</style>
