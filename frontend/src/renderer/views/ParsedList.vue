<template>
  <div class="parsed-list-container">
    <div class="list-content" v-loading="loading">
      <!-- 全选控制栏 -->
      <div v-if="selectionMode && pdfList.length > 0" class="selection-bar">
        <div class="selection-actions">
          <el-button type="primary" size="small" @click="handleConfirm">确认</el-button>
          <el-button size="small" @click="handleCancel">取消</el-button>
        </div>
        <el-checkbox
          v-model="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="handleSelectAllChange"
        >
          全选 (已选 {{ selectedPdfs.length }} / 共 {{ pdfList.length }})
        </el-checkbox>
      </div>

      <el-empty v-if="!loading && pdfList.length === 0" description="暂无已解析的PDF">
        <el-button type="primary" @click="goToUpload">上传PDF</el-button>
      </el-empty>

      <div v-else class="pdf-list">
        <div
          v-for="pdf in pdfList"
          :key="pdf.pdf_name"
          class="pdf-item"
        >
          <!-- 复选框 -->
          <div v-if="selectionMode" class="item-checkbox-wrapper" @click.stop>
            <el-checkbox
              :model-value="selectedPdfs.includes(pdf.pdf_name)"
              @change="(val) => toggleSelect(pdf.pdf_name, val)"
            />
          </div>

          <div class="item-icon" @click="openPDF(pdf.pdf_name)">
            <el-icon :size="32"><DocumentChecked /></el-icon>
          </div>
          <div class="item-content" @click="openPDF(pdf.pdf_name)">
            <h3 class="pdf-name" :title="pdf.pdf_name">{{ pdf.pdf_name }}</h3>
            <div class="pdf-meta">
              <span class="meta-item">
                <el-icon><Files /></el-icon>
                {{ pdf.total_pages }} 页
              </span>
              <span class="meta-divider">|</span>
              <span class="meta-item">
                <el-icon><Clock /></el-icon>
                {{ pdf.parsed_time }}
              </span>
              <span class="meta-divider">|</span>
              <span class="meta-item status-badge" :class="{ active: pdf.has_ocr }">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M12 3C7.03 3 3 7.03 3 12s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" :fill="pdf.has_ocr ? 'currentColor' : 'none'" :stroke="pdf.has_ocr ? 'none' : 'currentColor'" stroke-width="1.5"/>
                </svg>
                {{ pdf.has_ocr ? 'OCR已完成' : '未OCR' }}
              </span>
              <span class="meta-divider">|</span>
              <span class="meta-item status-badge" :class="getTranslationStatusClass(pdf)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M12.87 15.07L10.33 12.56L10.36 12.53C12.1 10.59 13.34 8.36 14.07 6H17V4H10V2H8V4H1V5.99H12.17C11.5 7.92 10.44 9.75 9 11.35C8.07 10.32 7.3 9.19 6.69 8H4.69C5.42 9.63 6.42 11.17 7.67 12.56L2.58 17.58L4 19L9 14L12.11 17.11L12.87 15.07Z" fill="currentColor"/>
                </svg>
                {{ getTranslationStatusText(pdf) }}
              </span>
            </div>
          </div>
          <div class="item-action">
            <Button2
              title="查看标注"
              aria-label="查看标注"
              @click="openPDF(pdf.pdf_name)"
            >
              <el-icon><View /></el-icon>
              <span>查看标注</span>
            </Button2>
            <Button2
              v-if="canEnterTranslation(pdf)" 
              title="查看翻译"
              aria-label="查看翻译"
              @click.stop="openTranslation(pdf.pdf_name)"
            >
              <el-icon><View /></el-icon>
              <span>查看翻译</span>
            </Button2>
            <div class="delete-action" @click.stop>
              <DeleteButton
                title="删除"
                aria-label="删除"
                @click="deletePDF(pdf.pdf_name)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导出模式选择对话框 -->
    <el-dialog
      v-model="downloadDialogVisible"
      title="选择导出模式"
      width="420px"
      :close-on-click-modal="false"
      class="download-mode-dialog"
    >
      <div class="download-mode-options">
        <div
          class="mode-option-card"
          :class="{ active: downloadMode === 'interleaved' }"
          @click="downloadMode = 'interleaved'"
        >
          <div class="mode-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
              <rect x="3" y="13" width="18" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6 6h6M6 16h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="mode-info">
            <h4>双语对照</h4>
            <p>一页原文、一页译文交替排列</p>
          </div>
          <div class="mode-check">
            <svg v-if="downloadMode === 'interleaved'" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>

        <div
          class="mode-option-card"
          :class="{ active: downloadMode === 'translation_only' }"
          @click="downloadMode = 'translation_only'"
        >
          <div class="mode-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="1" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6 8h12M6 12h10M6 16h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="mode-info">
            <h4>仅译文</h4>
            <p>只包含翻译后的文本内容</p>
          </div>
          <div class="mode-check">
            <svg v-if="downloadMode === 'translation_only'" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="downloadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isDownloading" @click="confirmDownload">
            确认导出
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DocumentChecked, Files, Clock, View } from '@element-plus/icons-vue'
import axios from 'axios'
import { getActiveTranslationTasks, exportPDF, getExportDownloadUrl, getExportList } from '../api/pdf'
import DeleteButton from '../elements/button/delete.vue'
import Button2 from '../elements/button/button2.vue'

const router = useRouter()
const loading = ref(false)
const pdfList = ref([])
const pendingReload = ref(false)
const activeTranslations = ref({}) // 活跃的翻译任务
let pollInterval = null // 轮询定时器

const props = defineProps({
  selectionMode: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['cancel', 'confirm-translate'])

// 选中状态
const selectedPdfs = ref([])

// 下载对话框状态
const downloadDialogVisible = ref(false)
const isDownloading = ref(false)
const currentDownloadPdfs = ref([])
const downloadMode = ref('interleaved') // 默认双语对照

const isAllSelected = computed({
  get: () => pdfList.value.length > 0 && selectedPdfs.value.length === pdfList.value.length,
  set: (val) => {
    selectedPdfs.value = val ? pdfList.value.map(p => p.pdf_name) : []
  }
})

const isIndeterminate = computed(() => {
  return selectedPdfs.value.length > 0 && selectedPdfs.value.length < pdfList.value.length
})

const handleSelectAllChange = (val) => {
  selectedPdfs.value = val ? pdfList.value.map(p => p.pdf_name) : []
}

const toggleSelect = (pdfName, val) => {
  if (val) {
    if (!selectedPdfs.value.includes(pdfName)) {
      selectedPdfs.value.push(pdfName)
    }
  } else {
    selectedPdfs.value = selectedPdfs.value.filter(name => name !== pdfName)
  }
}

// 监听选择模式变化，退出模式时清空选择
watch(() => props.selectionMode, (newVal) => {
  if (!newVal) {
    selectedPdfs.value = []
  }
})

const handleConfirm = () => {
  if (selectedPdfs.value.length === 0) {
    window.$toast?.warning('请先选择文件')
    return
  }
  if (props.selectionMode === 'download') {
    startBatchDownload()
  } else if (props.selectionMode === 'translate') {
    emit('confirm-translate')
  }
}

const handleCancel = () => {
  emit('cancel')
}

// 加载PDF列表
const loadList = async () => {
  if (loading.value) {
    pendingReload.value = true
    return
  }
  loading.value = true
  pendingReload.value = false
  try {
    const response = await axios.get('http://localhost:8000/api/v1/parsed-list')
    
    if (response.data.code === 200) {
      pdfList.value = response.data.data
      // 清空已选项（防止选中已不存在的文件）
      selectedPdfs.value = selectedPdfs.value.filter(name =>
        pdfList.value.some(p => p.pdf_name === name)
      )
      // 加载列表后立即检查活跃翻译
      await checkActiveTranslations()
    }
  } catch (error) {
    window.$toast?.error('加载PDF列表失败：' + error.message)
  } finally {
    loading.value = false
    if (pendingReload.value) {
      await loadList()
    }
  }
}

// 检查活跃的翻译任务
const checkActiveTranslations = async () => {
  try {
    const response = await getActiveTranslationTasks()
    if (response.code === 200) {
      activeTranslations.value = response.data || {}
    }
  } catch (error) {
    console.error('获取活跃翻译任务失败:', error)
  }
}

// 启动定时轮询
const startPolling = () => {
  if (pollInterval) return
  let previousActiveCount = 0  // 记录上一次的活跃任务数量
  let consecutiveEmptyCount = 0  // 连续空闲计数
  
  // 每2秒检查一次活跃翻译
  pollInterval = setInterval(async () => {
    await checkActiveTranslations()
    const currentActiveCount = Object.keys(activeTranslations.value).length
    
    // 如果有活跃翻译，刷新列表
    if (currentActiveCount > 0) {
      await loadList()
      consecutiveEmptyCount = 0  // 重置空闲计数
    }
    // 【关键优化】如果活跃任务数量从有变为无（翻译刚完成），再刷新一次列表以更新最终状态
    else if (previousActiveCount > 0 && currentActiveCount === 0) {
      console.log('检测到翻译任务完成，刷新列表以更新状态')
      await loadList()
      consecutiveEmptyCount = 0
    }
    // 【新增】翻译完成后的一段时间内，继续刷新几次以确保数据同步
    else if (previousActiveCount === 0 && currentActiveCount === 0 && consecutiveEmptyCount < 3) {
      consecutiveEmptyCount++
      if (consecutiveEmptyCount <= 2) {
        console.log(`翻译完成后的额外刷新 (${consecutiveEmptyCount}/2)`)
        await loadList()
      }
    }
    
    previousActiveCount = currentActiveCount
  }, 2000)
}

// 停止轮询
const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

// 打开PDF标注页面
const openPDF = (pdfName) => {
  router.push({
    path: '/annotation',
    query: {
      pdfName: pdfName
    }
  })
}

// 打开翻译界面
const openTranslation = (pdfName) => {
  router.push({
    path: '/translation',  // 修正路径
    query: {
      pdfName: pdfName
    }
  })
}

// 获取翻译状态的样式类
const getTranslationStatusClass = (pdf) => {
  // 【优化】使用后端提供的明确状态
  if (pdf.translation_status === 'completed') {
    return 'active completed'  // 已完成
  }
  
  // 检查是否有活跃翻译任务（正在翻译）
  const activeTask = activeTranslations.value[pdf.pdf_name]
  if (activeTask && activeTask.stage === 'running') {
    return 'active translating'  // 正在翻译中（脉冲动画）
  }
  
  if (pdf.translation_status === 'in_progress') {
    return 'active in-progress'  // 部分完成
  }
  
  return 'inactive'  // 未翻译
}

// 获取翻译状态文本
const getTranslationStatusText = (pdf) => {
  // 【优化】使用后端提供的明确状态
  if (pdf.translation_status === 'completed' && pdf.translation_progress) {
    const { total } = pdf.translation_progress
    return `已完成 (${total}/${total})`
  }
  
  // 检查是否有活跃翻译任务（正在翻译）
  const activeTask = activeTranslations.value[pdf.pdf_name]
  if (activeTask && activeTask.stage === 'running') {
    const progress = Math.round(activeTask.progress || 0)
    return `翻译中 ${progress}% (${activeTask.current || 0}/${activeTask.total || 0})`
  }
  
  if (pdf.translation_status === 'in_progress' && pdf.translation_progress) {
    const { completed, total } = pdf.translation_progress
    return `翻译中 (${completed}/${total})`
  }
  
  return '未翻译'
}

// 判断是否可以进入翻译界面
const canEnterTranslation = (pdf) => {
  // 【优化】只要有翻译结果文件就可以进入（包括 in_progress 和 completed）
  return pdf.translation_status === 'in_progress' || pdf.translation_status === 'completed'
}

// 删除PDF
const deletePDF = async (pdfName) => {
  try {
    const response = await axios.delete(`http://localhost:8000/api/v1/pdf/${pdfName}`)
    
    if (response.data.code === 200) {
      window.$toast?.success('删除成功')
      // 重新加载列表
      await loadList()
    }
  } catch (error) {
    window.$toast?.error('删除失败：' + error.message)
  }
}

// 跳转到上传页面
const goToUpload = () => {
  router.push('/')
}

// 初始化
onMounted(() => {
  loadList()
  startPolling()  // 启动轮询
  window.addEventListener('oceanpdf:parsed-list:refresh', loadList)
})

onUnmounted(() => {
  stopPolling()  // 停止轮询
  window.removeEventListener('oceanpdf:parsed-list:refresh', loadList)
})

// 开始批量下载
const startBatchDownload = () => {
  const completed = selectedPdfs.value.filter(name => {
    const pdf = pdfList.value.find(p => p.pdf_name === name)
    return pdf && pdf.translation_status === 'completed'
  })
  if (completed.length === 0) {
    window.$toast?.warning('请选择已完成翻译的文件')
    return
  }
  currentDownloadPdfs.value = completed
  downloadMode.value = 'interleaved'
  downloadDialogVisible.value = true
}

// 确认下载（支持批量）
const confirmDownload = async () => {
  const pdfs = currentDownloadPdfs.value
  if (!pdfs || pdfs.length === 0) return

  isDownloading.value = true
  window.$toast?.info(`正在导出 ${pdfs.length} 个PDF...`)

  let successCount = 0
  let failCount = 0

  for (const pdfName of pdfs) {
    try {
      const res = await exportPDF(pdfName, {
        mode: downloadMode.value,
        use_dps: false
      })
      if (res.code === 200 && res.data) {
        const { filename } = res.data
        const url = getExportDownloadUrl(filename)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        successCount++
      } else {
        throw new Error(res.message || '导出失败')
      }
    } catch (error) {
      console.error(`导出失败 [${pdfName}]:`, error)
      failCount++
    }
  }

  if (failCount === 0) {
    window.$toast?.success(`成功导出 ${successCount} 个文件`)
  } else {
    window.$toast?.warning(`成功 ${successCount} 个，失败 ${failCount} 个`)
  }

  downloadDialogVisible.value = false
  isDownloading.value = false
  emit('cancel')
}

// 暴露方法给父组件
defineExpose({
  loadList,
  selectedPdfs,
  pdfList,
  startBatchDownload
})
</script>

<style scoped lang="scss">
.parsed-list-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.selection-bar {
  padding: 12px 32px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 10;

  .selection-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  :deep(.el-checkbox__label) {
    font-size: 14px;
    color: #606266;
  }
}

.pdf-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.pdf-item {
  background: white;
  padding: 20px 32px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 20px;
  border-bottom: 1px solid #f0f0f0;

  &:hover {
    background: #fafafa;
    
    .item-action {
      opacity: 1;
    }
  }

  &:last-child {
    border-bottom: none;
  }

  .item-icon {
    color: #409eff;
    flex-shrink: 0;
  }

  .item-content {
    flex: 1;
    min-width: 0;

    .pdf-name {
      margin: 0 0 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .pdf-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: #909399;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 6px;

        .el-icon {
          font-size: 14px;
        }
      }

      .meta-divider {
        color: #dcdfe6;
      }
      
      .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        transition: all 0.2s;
        
        &.inactive {
          color: #909399;
          background: #f4f4f5;
        }
        
        &.active {
          color: #67c23a;
          background: #f0f9ff;
          
          svg {
            color: #67c23a;
          }
          
          &.translating {
            color: #409eff;
            background: #ecf5ff;
            animation: pulse 2s ease-in-out infinite;
            
            svg {
              color: #409eff;
            }
          }
          
          &.in-progress {
            color: #e6a23c;
            background: #fdf6ec;
            
            svg {
              color: #e6a23c;
            }
          }
          
          &.completed {
            color: #67c23a;
            background: #f0f9ff;
            
            svg {
              color: #67c23a;
            }
          }
        }
      }
    }
  }

  .item-checkbox-wrapper {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
  }

  .item-action {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    opacity: 0.6;
    transition: opacity 0.2s;
  }

  .delete-action {
    position: relative;
    width: 55px;
    height: 55px;
    flex-shrink: 0;
    overflow: visible;
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }
}

// 动画效果
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

// 空状态样式
:deep(.el-empty) {
  padding: 60px 0;
}

// 下载模式对话框样式
.download-mode-dialog {
  :deep(.el-dialog__header) {
    font-weight: 600;
    font-size: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .download-mode-options {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 8px 4px;

    .mode-option-card {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 16px;
      border: 2px solid #e5e7eb;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.25s ease;
      background: white;

      &:hover {
        border-color: #c4b5fd;
        background: #faf5ff;
      }

      &.active {
        border-color: #8b5cf6;
        background: #f3e8ff;

        .mode-icon {
          color: #7c3aed;
        }

        .mode-check {
          background: #8b5cf6;
          border-color: #8b5cf6;
        }
      }

      .mode-icon {
        flex-shrink: 0;
        color: #9ca3af;
        transition: color 0.25s;
      }

      .mode-info {
        flex: 1;
        min-width: 0;

        h4 {
          margin: 0 0 4px 0;
          font-size: 15px;
          font-weight: 600;
          color: #1f2937;
        }

        p {
          margin: 0;
          font-size: 13px;
          color: #6b7280;
        }
      }

      .mode-check {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid #d1d5db;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: all 0.25s;

        svg {
          stroke: white;
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
}
</style>
