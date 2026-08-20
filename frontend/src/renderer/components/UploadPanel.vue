<template>
  <div class="upload-panel" :class="{ 'has-files': items.length > 0 }">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      class="upload-area"
      :class="{ 'compact-mode': items.length > 0 }"
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      :multiple="true"
      accept=".pdf"
    >
      <div class="upload-content">
        <el-icon class="upload-icon">
          <UploadFilled />
        </el-icon>
        <div class="upload-text" v-if="items.length === 0">
          <p class="main-text">拖拽PDF文件到此处</p>
          <p class="sub-text">或</p>
          <el-button type="primary" size="large" class="upload-btn">
            选择文件上传
          </el-button>
        </div>
        <div class="upload-text compact" v-else>
          <el-button type="primary" class="upload-btn-compact">
            <el-icon><Plus /></el-icon>
            继续添加文件
          </el-button>
        </div>
        <div class="upload-tips" v-if="items.length === 0">
          <p>支持格式：PDF</p>
          <p>文件大小：最大 100MB</p>
        </div>
      </div>
    </el-upload>

    <!-- 解析服务选择 -->
    <div class="parser-bar">
      <span class="parser-label">解析服务</span>
      <el-select
        v-model="selectedParser"
        size="small"
        class="parser-select"
        :disabled="uploading"
      >
        <el-option label="本地DPS（默认）" value="dps" />
        <el-option
          v-for="p in externalParsers"
          :key="p.id"
          :label="`${p.emoji} ${p.name}${p.configured ? '' : '（未配置，请先去设置页配置）'}`"
          :value="p.id"
          :disabled="!p.configured"
        />
      </el-select>
      <span v-if="selectedParser !== 'dps'" class="parser-tip">外部服务按页计费，请留意用量</span>
    </div>

    <!-- 已选择文件显示 -->
    <transition name="file-list-fade">
      <div v-if="items.length > 0" class="file-info">
      <div class="file-list">
        <div v-for="item in items" :key="item.uid" class="file-item">
          <el-icon class="file-icon">
            <Document />
          </el-icon>
          <div class="file-details">
            <p class="file-name" :title="item.name">{{ item.name }}</p>
            <p class="file-size">
              {{ formatFileSize(item.size) }}
              <span v-if="item.statusText" class="file-status">｜{{ item.statusText }}</span>
            </p>
            <div v-if="item.progressVisible" class="progress-row">
              <el-progress 
                :percentage="item.progress" 
                :stroke-width="10"
                :color="getProgressColor(item)"
                :show-text="true"
                :format="() => `${item.progress}%`"
              />
            </div>
          </div>
          <div class="ocr-toggle">
            <span class="ocr-label">OCR</span>
            <el-switch v-model="item.ocrEnabled" :disabled="uploading" />
          </div>
          <el-button
            type="danger"
            :icon="Delete"
            circle
            size="small"
            :disabled="uploading"
            @click="removeItem(item.uid)"
          />
        </div>
      </div>

      <!-- 上传按钮 -->
      <div class="action-buttons">
        <el-button
          type="primary"
          size="large"
          :loading="uploading"
          @click="handleUpload"
        >
          {{ uploading ? '解析中...' : items.length === 1 ? '开始翻译' : '开始批量解析' }}
        </el-button>
        <el-button size="large" :disabled="uploading" @click="clearAll">
          清空列表
        </el-button>
      </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Document, Delete, Plus } from '@element-plus/icons-vue'
import { uploadPDF, getDocumentParserStatus } from '../api/pdf'

const router = useRouter()
const uploadRef = ref(null)
const uploading = ref(false)

// 版面分析服务选择（dps=本地DPS，其余为外部服务ID）
const selectedParser = ref('dps')
const externalParsers = ref([])

const loadParserStatus = async () => {
  try {
    const res = await getDocumentParserStatus()
    const list = res?.data ?? []
    externalParsers.value = Array.isArray(list) ? list : []
  } catch (e) {
    console.warn('[UploadPanel] 获取解析服务状态失败:', e)
  }
}

onMounted(() => {
  loadParserStatus()
})

const props = defineProps({
  parallelism: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['go-parsed'])

const rawItems = ref([])

const items = computed(() => {
  return rawItems.value.map((it) => {
    const statusTextMap = {
      pending: '等待解析',
      uploading: '文件上传中',
      processing: it.ocrEnabled ? 'OCR识别中' : '版面分析中',
      done: '完成',
      exists: '已存在',
      error: '失败'
    }
    const statusText = statusTextMap[it.status] || ''
    const progressVisible = it.status === 'uploading' || it.status === 'processing'
    it.statusText = statusText
    it.progressVisible = progressVisible
    return it
  })
})

// 进度条颜色
const getProgressColor = (item) => {
  if (item.status === 'uploading') {
    // 上传阶段（0-20%）- 蓝色
    return '#409EFF'
  } else if (item.status === 'processing') {
    // 解析阶段（20-100%）- 渐变色
    return [
      { color: '#667eea', percentage: 50 },
      { color: '#764ba2', percentage: 100 }
    ]
  }
  return '#67C23A' // 默认绿色
}

// 文件选择处理
const handleFileChange = (file) => {
  const raw = file?.raw
  if (!raw) return

  // 验证文件类型
  if (!raw.name.toLowerCase().endsWith('.pdf')) {
    window.$toast?.error('只支持PDF格式文件')
    return
  }

  // 验证文件大小 (100MB)
  const maxSize = 100 * 1024 * 1024
  if (raw.size > maxSize) {
    window.$toast?.error('文件大小不能超过 100MB')
    return
  }

  const key = `${raw.name}__${raw.size}__${raw.lastModified}`
  const exists = rawItems.value.some((it) => it.key === key)
  if (exists) {
    window.$toast?.warning('已在列表中：' + raw.name)
    return
  }

  rawItems.value.push({
    uid: file.uid,
    key,
    file: raw,
    name: raw.name,
    size: raw.size,
    ocrEnabled: false,
    status: 'pending',
    progress: 0,
    result: null,
    error: null
  })

  console.log('[UploadPanel] 添加文件:', {
    name: raw.name,
    size: raw.size,
    lastModified: raw.lastModified,
    totalSelected: rawItems.value.length
  })
}

const removeItem = (uid) => {
  rawItems.value = rawItems.value.filter((it) => it.uid !== uid)
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const clearAll = () => {
  rawItems.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const clampParallelism = () => {
  const n = Number(props.parallelism)
  if (!Number.isFinite(n)) return 1
  return Math.max(1, Math.min(5, Math.floor(n)))
}

const uploadOne = async (item) => {
  item.status = 'uploading'
  item.progress = 0
  item.error = null
  item.result = null

  // 生成task_id
  const taskId = `${Date.now()}_${Math.random().toString(36).substring(7)}`
  
  console.log('[UploadPanel] 开始触析:', {
    name: item.name,
    size: item.size,
    with_ocr: item.ocrEnabled,
    parser: selectedParser.value,
    taskId
  })

  // SSE连接和完成信号
  let eventSource = null
  let uploadPromise = null
  let sseCompleted = false
  let sseCompletedResolve = null
  
  // 创建SSE完成Promise
  const sseCompletedPromise = new Promise((resolve) => {
    sseCompletedResolve = resolve
  })

  try {
    // 启动SSE进度推送
    const baseURL = 'http://localhost:8000'
    eventSource = new EventSource(`${baseURL}/api/v1/upload/progress/${taskId}`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const { progress, stage, message } = data
        
        console.log('[SSE] 进度更新:', { progress, stage, message })
        
        // 更新进度
        item.progress = progress
        
        // 更新状态
        if (stage === 'uploading' || stage === 'uploaded') {
          item.status = 'uploading'
        } else if (stage === 'parsing' || stage === 'dps' || stage === 'annotation') {
          item.status = 'processing'
        } else if (stage === 'completed') {
          item.status = 'done'
          sseCompleted = true
          sseCompletedResolve?.(true)  // 触发完成信号
        } else if (stage === 'error') {
          item.status = 'error'
          item.error = message
          sseCompleted = true
          sseCompletedResolve?.(false)  // 触发错误信号
        }
      } catch (e) {
        console.error('[SSE] 解析数据失败:', e)
      }
    }
    
    eventSource.onerror = (error) => {
      console.error('[SSE] 连接错误:', error)
      eventSource?.close()
      // SSE连接错误不一定是失败，可能是正常关闭
      if (!sseCompleted) {
        console.warn('[SSE] 连接意外断开，等待上传结果')
      }
    }

    // 阶段1: 文件上传（0-15%）
    uploadPromise = uploadPDF(item.file, {
      withOcr: item.ocrEnabled,
      parser: selectedParser.value,  // 传递所选版面分析服务
      taskId: taskId,  // 传递taskId
      onProgress: (p) => {
        // 将上传进度映射到 0-15%
        const mappedProgress = Math.floor(p * 0.15)
        if (mappedProgress > item.progress) {
          item.progress = mappedProgress
        }
      }
    })

    const response = await uploadPromise
    const result = response?.data ?? response
    item.result = result
    if (response?.data && !result?.pdf_name) {
      console.warn('[UploadPanel] 响应包含data但缺少pdf_name:', { response, data: response?.data })
    }
    
    console.log('[UploadPanel] HTTP请求完成，等待SSE推送完成信号...')
    
    // 等待SSE推送完成信号，不设置超时限制
    // 只有当SSE推送completed或error时才结束等待
    const sseSuccess = await sseCompletedPromise
    
    // 根据SSE结果设置最终状态
    if (sseSuccess === true) {
      // SSE推送了completed
      item.status = result?.already_exists ? 'exists' : 'done'
      item.progress = 100
      console.log('[UploadPanel] SSE确认完成')
    } else if (sseSuccess === false) {
      // SSE推送了error
      console.log('[UploadPanel] SSE报告错误')
      // error信息已在onmessage中设置
    }

    try {
      window.dispatchEvent(
        new CustomEvent('oceanpdf:parsed-list:refresh', {
          detail: { pdfName: result?.pdf_name }
        })
      )
    } catch (e) {
      console.error('[UploadPanel] 触发列表刷新事件失败:', e)
    }

    console.log('[UploadPanel] 解析完成:', {
      name: item.name,
      pdf_name: result?.pdf_name,
      total_pages: result?.total_pages,
      already_exists: result?.already_exists,
      with_ocr: result?.with_ocr,
      final_status: item.status
    })
  } catch (error) {
    const msg = error?.message || '未知错误'
    item.status = 'error'
    item.error = msg
    item.progress = Math.min(item.progress || 0, 99)
    console.error('[UploadPanel] 触析失败:', { name: item.name, err: error })
  } finally {
    // 关闭SSE连接
    if (eventSource) {
      eventSource.close()
      console.log('[SSE] 连接关闭')
    }
  }
}

const runWithConcurrency = async (targets, concurrency) => {
  const queue = targets.slice()
  const workers = new Array(concurrency).fill(0).map(async (_, idx) => {
    while (queue.length > 0) {
      const next = queue.shift()
      if (!next) return
      console.log('[UploadPanel] worker开始处理:', { worker: idx + 1, name: next.name })
      await uploadOne(next)
      console.log('[UploadPanel] worker处理结束:', { worker: idx + 1, name: next.name, status: next.status })
    }
  })
  await Promise.all(workers)
}

// 上传文件
const handleUpload = async () => {
  if (rawItems.value.length === 0) {
    window.$toast?.warning('请先选择文件')
    return
  }

  uploading.value = true
  
  try {
    const concurrency = clampParallelism()
    const targets = rawItems.value.filter((it) => it.status === 'pending' || it.status === 'error')
    console.log('[UploadPanel] 批量解析启动:', {
      total: rawItems.value.length,
      targets: targets.length,
      concurrency
    })

    await runWithConcurrency(targets, concurrency)

    const doneCount = rawItems.value.filter((it) => it.status === 'done').length
    const existsCount = rawItems.value.filter((it) => it.status === 'exists').length
    const errorCount = rawItems.value.filter((it) => it.status === 'error').length
    console.log('[UploadPanel] 批量解析汇总:', { doneCount, existsCount, errorCount })

    if (rawItems.value.length === 1) {
      const only = rawItems.value[0]
      const result = only?.result
          
      // 检查是否成功
      if (only.status === 'error') {
        const errorMsg = only.error || '未知错误'
        window.$toast?.error(`解析失败：${errorMsg}`)
        return
      }
          
      if (!result?.pdf_name) {
        window.$toast?.error('解析失败：未获取到pdf_name，请查看后端日志')
        console.error('[UploadPanel] result数据异常:', { result, status: only.status })
        return
      }
          
      if (result.already_exists) {
        window.$toast?.info('此PDF已解析过，直接打开标注页面')
      } else {
        window.$toast?.success(`上传成功！解析完成 ${result.total_pages} 页`)
      }
      setTimeout(() => {
        router.push({
          path: '/annotation',
          query: { pdfName: result.pdf_name }
        })
      }, 500)
      return
    }

    if (errorCount === 0) {
      window.$toast?.success(`批量解析完成：成功 ${doneCount}，已存在 ${existsCount}`)
    } else {
      window.$toast?.warning(`批量解析完成：成功 ${doneCount}，已存在 ${existsCount}，失败 ${errorCount}`)
    }
    emit('go-parsed')
    
  } catch (error) {
    window.$toast?.error('上传失败：' + (error.message || '未知错误'))
    console.error('上传错误:', error)
  } finally {
    uploading.value = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
</script>

<style scoped lang="scss">
.upload-panel {
  width: 100%;
  height: 100%;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 0;
  gap: 20px;

  &.has-files {
    justify-content: flex-start;
    gap: 16px;
  }
}

.upload-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  :deep(.el-upload) {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    height: 100%;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d9d9d9;
    border-radius: 16px;
    background: white;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      border-color: #667eea;
      background: #fafbff;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  // 紧凑模式样式
  &.compact-mode {
    :deep(.el-upload-dragger) {
      min-height: 100px;
      border-style: solid;
      border-width: 1px;
      background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);

      &:hover {
        border-color: #667eea;
        background: linear-gradient(135deg, #f0f2ff 0%, #fafbff 100%);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
      }
    }
  }
}

// 解析服务选择栏
.parser-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: white;
  border-radius: 10px;
  border: 1px solid #e8ecf4;
  box-shadow: 0 1px 4px rgba(102, 126, 234, 0.06);

  .parser-label {
    font-size: 13px;
    font-weight: 600;
    color: #4a5568;
    white-space: nowrap;
  }

  .parser-select {
    width: 260px;
  }

  .parser-tip {
    font-size: 12px;
    color: #e6a23c;
    white-space: nowrap;
  }
}

.upload-content {
  text-align: center;
  padding: clamp(20px, 5vh, 40px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;

  .upload-icon {
    font-size: clamp(48px, 8vh, 72px);
    color: #667eea;
    margin-bottom: clamp(12px, 3vh, 24px);
    opacity: 0.9;
    transition: all 0.3s;
  }

  // 紧凑模式下的图标
  .compact-mode & {
    padding: 20px;

    .upload-icon {
      font-size: 32px;
      margin-bottom: 0;
      display: none;
    }
  }

  .upload-text {
    &:not(.compact) {
      .main-text {
        font-size: clamp(16px, 2vh, 18px);
        font-weight: 500;
        color: #1a1a1a;
        margin-bottom: clamp(8px, 1.5vh, 12px);
      }

      .sub-text {
        font-size: clamp(12px, 1.5vh, 14px);
        color: #999;
        margin: clamp(8px, 2vh, 16px) 0;
      }

      .upload-btn {
        margin-top: clamp(8px, 1.5vh, 12px);
        padding: 10px 20px;
        font-size: clamp(16px, 2vh, 24px);
        font-weight: bold;
        text-align: center;
        color: #fff;
        background-color: #4F6BFF;
        border: 2px solid #000;
        border-radius: 10px;
        box-shadow: 5px 5px 0px #000;
        transition: all 0.3s ease;
        cursor: pointer;

        &:hover {
          background-color: #fff;
          color: #4F6BFF;
          border: 2px solid #4F6BFF;
          box-shadow: 5px 5px 0px #4F6BFF;
        }

        &:active {
          background-color: #8EA1FF;
          box-shadow: none;
          transform: translateY(4px);
        }
      }
    }

    &.compact {
      .upload-btn-compact {
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        color: #fff;
        background-color: #4F6BFF;
        border: 2px solid #000;
        border-radius: 10px;
        box-shadow: 5px 5px 0px #000;
        transition: all 0.3s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;

        .el-icon {
          font-size: 16px;
        }

        &:hover {
          background-color: #fff;
          color: #4F6BFF;
          border: 2px solid #4F6BFF;
          box-shadow: 5px 5px 0px #4F6BFF;
        }

        &:active {
          background-color: #8EA1FF;
          box-shadow: none;
          transform: translateY(4px);
        }
      }
    }
  }

  .upload-tips {
    margin-top: clamp(16px, 4vh, 32px);
    padding-top: clamp(12px, 3vh, 24px);
    border-top: 1px solid #f0f0f0;

    p {
      font-size: clamp(12px, 1.5vh, 13px);
      color: #999;
      line-height: 2;
      margin: 0;
    }
  }
}

.file-info {
  padding: clamp(16px, 3vh, 24px);
  background: white;
  border-radius: 16px;
  border: 1px solid #e8e8e8;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  .file-list {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
    margin-bottom: 16px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f5f5f5;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #d0d0d0;
      border-radius: 3px;

      &:hover {
        background: #b0b0b0;
      }
    }
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: clamp(12px, 2vh, 16px);
    padding: clamp(16px, 2.5vh, 20px);
    background: #fafafa;
    border-radius: 12px;
    margin-bottom: clamp(16px, 3vh, 24px);
    border: 1px solid #f0f0f0;

    .file-icon {
      font-size: clamp(32px, 5vh, 40px);
      color: #f56c6c;
    }

    .file-details {
      flex: 1;

      .file-name {
        font-size: clamp(14px, 1.8vh, 15px);
        font-weight: 500;
        color: #1a1a1a;
        margin-bottom: clamp(6px, 1vh, 8px);
        word-break: break-all;
      }

      .file-size {
        font-size: clamp(12px, 1.5vh, 13px);
        color: #999;
      }

      .file-status {
        color: #666;
      }

      .progress-row {
        margin-top: 10px;
        max-width: 520px;
        
        :deep(.el-progress__text) {
          font-size: 12px !important;
          font-weight: 500;
        }
        
        :deep(.el-progress-bar__outer) {
          border-radius: 5px;
          overflow: hidden;
        }
        
        :deep(.el-progress-bar__inner) {
          border-radius: 5px;
          transition: width 0.3s ease, background-color 0.3s ease;
        }
      }
    }

    .ocr-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;

      .ocr-label {
        font-size: 13px;
        color: #606266;
        user-select: none;
      }
    }
  }

  .action-buttons {
    flex-shrink: 0;
    display: flex;
    justify-content: center;
    gap: clamp(12px, 2vh, 16px);
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;

    .el-button {
      padding: clamp(10px, 1.5vh, 12px) clamp(24px, 4vw, 32px);
      font-size: clamp(14px, 1.8vh, 15px);
      border-radius: 8px;

      &.el-button--primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;

        &:hover {
          opacity: 0.9;
        }
      }
    }
  }
}

// 文件列表淡入淡出动画
.file-list-fade-enter-active,
.file-list-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-list-fade-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.file-list-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
