<template>
  <div class="extract-workbench" :class="{ 'has-files': file }">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      class="upload-area"
      :class="{ 'compact-mode': file }"
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      accept=".pdf,application/pdf"
    >
      <div class="upload-content">
        <el-icon class="upload-icon">
          <UploadFilled />
        </el-icon>
        <div v-if="!file" class="upload-text">
          <p class="main-text">拖拽 PDF 文件到此处</p>
          <p class="sub-text">或</p>
          <el-button type="primary" size="large" class="upload-btn">
            选择文件上传
          </el-button>
        </div>
        <div v-else class="upload-text compact">
          <el-button type="primary" class="upload-btn-compact">
            <el-icon><RefreshLeft /></el-icon>
            重新选择文件
          </el-button>
        </div>
        <div v-if="!file" class="upload-tips">
          <p>支持格式：PDF</p>
          <p>第一步选择要提取的页面，第二步调整提取后的顺序</p>
        </div>
      </div>
    </el-upload>

    <!-- 提取工作区 -->
    <transition name="file-list-fade">
      <div v-if="file" class="file-panel">
        <div class="panel-header-row">
          <div class="panel-title">
            <el-icon><Postcard /></el-icon>
            <span>提取设置</span>
          </div>
          <span class="file-count">{{ totalPages || '?' }} 页</span>
        </div>

        <div class="file-row">
          <el-icon class="file-icon"><Document /></el-icon>
          <div class="file-details">
            <p class="file-name" :title="file.name">{{ file.name }}</p>
            <p class="file-size">{{ formatFileSize(file.size) }}</p>
          </div>
        </div>

        <!-- 步骤指示器 -->
        <div class="step-indicator">
          <div class="step-item" :class="{ active: step === 1, done: step > 1 }">
            <span class="step-num">
              <el-icon v-if="step > 1"><Check /></el-icon>
              <template v-else>1</template>
            </span>
            <span class="step-label">选择提取页面</span>
          </div>
          <div class="step-line" :class="{ active: step > 1 }"></div>
          <div class="step-item" :class="{ active: step === 2 }">
            <span class="step-num">2</span>
            <span class="step-label">调整顺序</span>
          </div>
        </div>

        <div v-if="previewing" class="preview-loading">
          <div class="spinner"></div>
          <p>正在生成页面预览，请稍候...</p>
        </div>

        <div v-else-if="previewError" class="preview-error">
          <el-icon><WarningFilled /></el-icon>
          <p>{{ previewError }}</p>
          <div class="preview-error-actions">
            <el-button size="small" @click="loadPreview">重试</el-button>
          </div>
        </div>

        <!-- ============ 第一步：选择要提取的页面 ============ -->
        <template v-else-if="step === 1">
          <div class="visual-toolbar">
            <span class="select-progress">
              已选 <span class="accent-count">{{ selected.size }}</span> 页
            </span>
            <div class="toolbar-actions">
              <el-button size="small" :disabled="selected.size === totalPages" @click="selectAll">
                全选
              </el-button>
              <el-button size="small" :disabled="selected.size === 0" @click="clearSelection">
                清空选择
              </el-button>
            </div>
          </div>

          <p class="visual-hint">点击缩略图选择要提取的页面（按住 Shift 可连续多选）</p>

          <div class="page-grid">
            <div
              v-for="t in thumbnails"
              :key="t.page"
              class="page-card"
              :class="{ 'is-selected': selected.has(t.page) }"
              :title="`选择第 ${t.page} 页`"
              @click="togglePage(t.page, $event)"
            >
              <img :src="t.image" :alt="`第 ${t.page} 页`" draggable="false" />
              <span class="page-num">{{ t.page }}</span>
              <span v-if="selected.has(t.page)" class="page-check">
                <el-icon><Check /></el-icon>
              </span>
            </div>
          </div>
        </template>

        <!-- ============ 第二步：调整提取后的顺序 ============ -->
        <template v-else>
          <div class="visual-toolbar">
            <span class="select-progress">
              共 <span class="accent-count">{{ orderedPages.length }}</span> 页 · 新顺序：{{ orderText }}
            </span>
            <div class="toolbar-actions">
              <el-button size="small" :disabled="isOriginalOrder" @click="resetOrder">
                按原页码排序
              </el-button>
            </div>
          </div>

          <p class="visual-hint">拖动页面卡片调整提取后的顺序，生成时按此顺序输出</p>

          <div class="page-grid">
            <div
              v-for="(page, index) in orderedPages"
              :key="page"
              class="page-card"
              :class="{ 'is-dragging': dragIndex === index }"
              draggable="true"
              @dragstart="onDragStart($event, index)"
              @dragover.prevent="onDragOver(index)"
              @drop.prevent
              @dragend="onDragEnd"
            >
              <img :src="thumbMap[page]?.image" :alt="`第 ${page} 页`" draggable="false" />
              <span class="page-order-num">{{ index + 1 }}</span>
              <span class="page-origin-num">原 {{ page }}</span>
            </div>
          </div>
        </template>

        <div class="action-buttons">
          <template v-if="step === 1">
            <el-button
              type="primary"
              size="large"
              :disabled="selected.size === 0"
              @click="goNext"
            >
              下一步（{{ selected.size }} 页）
            </el-button>
            <el-button size="large" :disabled="previewing" @click="clearFile">
              清空
            </el-button>
          </template>
          <template v-else>
            <el-button size="large" :disabled="submitting" @click="goBack">
              上一步
            </el-button>
            <el-button
              class="generate-btn"
              type="primary"
              size="large"
              :loading="submitting"
              @click="handleGenerate"
            >
              {{ submitting ? '生成中...' : '生成并下载' }}
            </el-button>
          </template>
        </div>
      </div>
    </transition>

    <!-- 处理结果 -->
    <div v-if="results.length" class="result-panel">
      <div class="results-header">
        <div class="results-title">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>处理完成</span>
        </div>
      </div>
      <div v-for="r in results" :key="r.filename" class="result-item">
        <el-icon class="result-icon"><Document /></el-icon>
        <span class="result-name" :title="r.filename">{{ r.filename }}</span>
        <el-button type="primary" size="small" @click="downloadOutput(r)">下载</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  UploadFilled,
  Document,
  Postcard,
  RefreshLeft,
  CircleCheckFilled,
  Check,
  WarningFilled
} from '@element-plus/icons-vue'
import { extractPages, previewPDF, getToolDownloadUrl } from '../api/tools'

const uploadRef = ref(null)
const file = ref(null)
const submitting = ref(false)
const results = ref([])

// 步骤：1 选择提取页面 / 2 调整顺序
const step = ref(1)

// 预览状态
const previewing = ref(false)
const previewError = ref('')
const totalPages = ref(0)
const thumbnails = ref([])

// 第一步：选择状态
const selected = ref(new Set())
const lastClicked = ref(0)

// 第二步：提取后的页面顺序
const orderedPages = ref([])
const dragIndex = ref(-1)

// 页码 -> 缩略图
const thumbMap = computed(() => {
  const map = {}
  for (const t of thumbnails.value) {
    map[t.page] = t
  }
  return map
})

const isOriginalOrder = computed(() => {
  const sorted = [...orderedPages.value].sort((a, b) => a - b)
  return orderedPages.value.every((p, i) => p === sorted[i])
})

const orderText = computed(() => {
  if (!orderedPages.value.length) return '-'
  return orderedPages.value.join(', ')
})

// ---------- 文件选择 ----------
const handleFileChange = (uploadFile) => {
  const raw = uploadFile?.raw
  if (!raw) return

  if (!raw.name.toLowerCase().endsWith('.pdf')) {
    window.$toast?.error('只支持 PDF 格式文件')
    return
  }

  const maxSize = 100 * 1024 * 1024
  if (raw.size > maxSize) {
    window.$toast?.error('文件大小不能超过 100MB')
    return
  }

  if (file.value && file.value.key === `${raw.name}__${raw.size}__${raw.lastModified}`) {
    window.$toast?.warning('已选择该文件：' + raw.name)
    return
  }

  file.value = {
    key: `${raw.name}__${raw.size}__${raw.lastModified}`,
    name: raw.name,
    size: raw.size,
    raw
  }
  results.value = []
  loadPreview()
}

const clearFile = () => {
  file.value = null
  results.value = []
  previewing.value = false
  previewError.value = ''
  totalPages.value = 0
  thumbnails.value = []
  selected.value = new Set()
  lastClicked.value = 0
  orderedPages.value = []
  dragIndex.value = -1
  step.value = 1
  uploadRef.value?.clearFiles()
}

// ---------- 预览生成 ----------
const loadPreview = async () => {
  if (!file.value) return
  previewing.value = true
  previewError.value = ''
  totalPages.value = 0
  thumbnails.value = []
  selected.value = new Set()
  lastClicked.value = 0
  orderedPages.value = []
  dragIndex.value = -1
  step.value = 1
  results.value = []

  try {
    const res = await previewPDF(file.value.raw)
    if (res && res.code === 200) {
      const data = res.data || {}
      totalPages.value = data.total_pages || 0
      thumbnails.value = data.pages || []
      window.$toast?.success(`已生成 ${totalPages.value} 页预览`)
    }
  } catch (e) {
    previewError.value = e?.response?.data?.detail || e?.message || '预览生成失败'
    window.$toast?.error(previewError.value)
  } finally {
    previewing.value = false
  }
}

// ---------- 第一步：页面选择 ----------
const togglePage = (page, event) => {
  const s = new Set(selected.value)
  if (event.shiftKey && lastClicked.value) {
    const [a, b] = [Math.min(lastClicked.value, page), Math.max(lastClicked.value, page)]
    for (let p = a; p <= b; p++) s.add(p)
  } else if (s.has(page)) {
    s.delete(page)
  } else {
    s.add(page)
  }
  lastClicked.value = page
  selected.value = s
}

const clearSelection = () => {
  selected.value = new Set()
  lastClicked.value = 0
}

const selectAll = () => {
  selected.value = new Set(Array.from({ length: totalPages.value }, (_, i) => i + 1))
}

// ---------- 步骤切换 ----------
const goNext = () => {
  if (selected.value.size === 0) {
    window.$toast?.warning('请先选择要提取的页面')
    return
  }
  orderedPages.value = [...selected.value].sort((a, b) => a - b)
  dragIndex.value = -1
  step.value = 2
}

const goBack = () => {
  step.value = 1
}

// ---------- 第二步：拖拽排序 ----------
const onDragStart = (e, index) => {
  dragIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

const onDragOver = (index) => {
  if (dragIndex.value === -1 || dragIndex.value === index) return
  const arr = orderedPages.value.slice()
  const [moved] = arr.splice(dragIndex.value, 1)
  arr.splice(index, 0, moved)
  orderedPages.value = arr
  dragIndex.value = index
}

const onDragEnd = () => {
  dragIndex.value = -1
}

const resetOrder = () => {
  orderedPages.value = [...orderedPages.value].sort((a, b) => a - b)
}

// ---------- 生成 ----------
const handleGenerate = async () => {
  if (!file.value) {
    window.$toast?.warning('请先选择 PDF 文件')
    return
  }
  if (!orderedPages.value.length) {
    window.$toast?.warning('请先选择要提取的页面')
    return
  }

  submitting.value = true
  results.value = []
  try {
    // 按当前顺序提取（等价于提取 + 重排）
    const spec = orderedPages.value.join(',')
    const res = await extractPages(file.value.raw, spec, { preserveOrder: true })
    if (res && res.code === 200) {
      results.value = res.data?.outputs || []
      window.$toast?.success('提取完成')
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('提取失败：' + msg)
  } finally {
    submitting.value = false
  }
}

const downloadOutput = (out) => {
  const link = document.createElement('a')
  link.href = getToolDownloadUrl(out.filename)
  link.download = out.filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// ---------- 格式化 ----------
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
</script>

<style scoped lang="scss">
.extract-workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 2px;
}

// 上传区域
.upload-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;

  :deep(.el-upload) {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    height: 100%;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d9d9d9;
    border-radius: 14px;
    background: white;
    transition: border-color 0.3s ease, background-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
      border-color: #667eea;
      background: #fafbff;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  &.compact-mode {
    :deep(.el-upload-dragger) {
      min-height: 96px;
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

.upload-content {
  text-align: center;
  padding: clamp(18px, 3.5vh, 32px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  .upload-icon {
    font-size: clamp(40px, 6.5vh, 60px);
    color: #667eea;
    margin-bottom: clamp(10px, 2vh, 18px);
    opacity: 0.9;
  }

  .compact-mode & {
    padding: 18px;

    .upload-icon {
      display: none;
    }
  }

  .upload-text {
    &:not(.compact) {
      .main-text {
        font-size: clamp(15px, 2vh, 17px);
        font-weight: 500;
        color: #1a1a1a;
        margin-bottom: clamp(8px, 1.5vh, 12px);
      }

      .sub-text {
        font-size: clamp(12px, 1.5vh, 13px);
        color: #999;
        margin: clamp(8px, 2vh, 14px) 0;
      }

      .upload-btn {
        margin-top: clamp(8px, 1.5vh, 12px);
        padding: 12px 30px;
        font-size: clamp(14px, 1.8vh, 17px);
        font-weight: 600;
        color: #fff;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(102, 126, 234, 0.35);
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 24px rgba(102, 126, 234, 0.42);
          filter: brightness(1.04);
        }

        &:active {
          transform: translateY(0);
          box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        }
      }
    }

    &.compact {
      .upload-btn-compact {
        padding: 9px 20px;
        font-size: 14px;
        font-weight: 600;
        color: #4f6bff;
        background: #fff;
        border: 1.5px solid rgba(79, 107, 255, 0.45);
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(79, 107, 255, 0.1);
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;

        .el-icon {
          font-size: 14px;
        }

        &:hover {
          background: #f0f2ff;
          border-color: #4f6bff;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(79, 107, 255, 0.16);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }
  }

  .upload-tips {
    margin-top: clamp(14px, 3vh, 22px);
    padding-top: clamp(10px, 2vh, 16px);
    border-top: 1px solid #f0f0f0;

    p {
      font-size: 12px;
      color: #999;
      line-height: 2;
      margin: 0;
    }
  }
}

// 工作区面板
.file-panel {
  padding: clamp(14px, 2.5vh, 20px);
  background: white;
  border-radius: 14px;
  border: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  .panel-header-row {
    display: flex;
    align-items: center;
    gap: 12px;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 15px;
      font-weight: 600;
      color: #1a1a1a;

      .el-icon {
        color: #0ea5e9;
        font-size: 18px;
      }
    }

    .file-count {
      margin-left: auto;
      font-size: 12px;
      font-weight: 500;
      color: #0ea5e9;
      background: rgba(14, 165, 233, 0.1);
      padding: 4px 10px;
      border-radius: 12px;
    }
  }

  .file-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 12px;

    .file-icon {
      flex: 0 0 auto;
      font-size: 26px;
      color: #f56c6c;
    }

    .file-details {
      flex: 1;
      min-width: 0;

      .file-name {
        font-size: 14px;
        font-weight: 500;
        color: #1a1a1a;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .file-size {
        font-size: 12px;
        color: #999;
      }
    }
  }

  // 步骤指示器
  .step-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #f8fafc;
    border: 1px solid #eef2f7;
    border-radius: 12px;

    .step-item {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #9ca3af;

      .step-num {
        width: 24px;
        height: 24px;
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        color: #fff;
        background: #cbd5e1;
        border-radius: 50%;
        transition: background-color 0.2s ease, transform 0.2s ease;
      }

      .step-label {
        font-size: 13px;
        font-weight: 500;
      }

      &.active {
        color: #0ea5e9;

        .step-num {
          background: #0ea5e9;
          box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.15);
        }
      }

      &.done {
        color: #10b981;

        .step-num {
          background: #10b981;
        }
      }
    }

    .step-line {
      flex: 1;
      height: 2px;
      background: #e2e8f0;
      border-radius: 1px;
      transition: background-color 0.2s ease;

      &.active {
        background: #10b981;
      }
    }
  }

  // 预览加载/错误
  .preview-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 36px 0;
    color: #909399;
    font-size: 13px;

    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid rgba(14, 165, 233, 0.2);
      border-top-color: #0ea5e9;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    p {
      margin: 0;
    }
  }

  .preview-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 28px 0;
    color: #f56c6c;
    font-size: 13px;
    text-align: center;

    .el-icon {
      font-size: 36px;
    }

    p {
      margin: 0;
      max-width: 460px;
    }

    .preview-error-actions {
      display: flex;
      gap: 10px;
    }
  }

  // 可视化工具栏
  .visual-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;

    .select-progress {
      font-size: 13px;
      font-weight: 500;
      color: #374151;

      .accent-count {
        color: #0ea5e9;
        font-weight: 700;
      }
    }

    .toolbar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;

      .el-button {
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 500;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        background: #f8f9fb;
        color: #4b5563;
        transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;

        &:hover:not(:disabled) {
          background: #ecfeff;
          border-color: #a5f3fc;
          color: #0ea5e9;
          transform: translateY(-1px);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }
      }
    }
  }

  .visual-hint {
    font-size: 12px;
    color: #9ca3af;
    margin: -4px 0 0;
  }

  // 页面缩略图网格
  .page-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100% / 4, 160px), 1fr));
    gap: 12px;
    max-height: 320px;
    overflow-y: auto;
    padding: 4px 6px 4px 2px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-thumb {
      background: #d0d0d0;
      border-radius: 3px;

      &:hover {
        background: #b0b0b0;
      }
    }
  }

  .page-card {
    position: relative;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    background: white;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease, opacity 0.15s ease;
    user-select: none;

    &::after {
      content: '';
      position: absolute;
      left: 50%;
      top: 50%;
      width: 24px;
      height: 24px;
      margin: -12px 0 0 -12px;
      border-radius: 50%;
      background: rgba(14, 165, 233, 0.4);
      opacity: 0;
      pointer-events: none;
    }

    &:active::after {
      animation: card-ripple 0.45s ease-out;
    }

    &:hover {
      border-color: #7dd3fc;
      box-shadow: 0 3px 10px rgba(14, 165, 233, 0.15);
      transform: translateY(-1px);
    }

    img {
      display: block;
      width: 100%;
      height: auto;
      pointer-events: none;
    }

    .page-num {
      position: absolute;
      left: 6px;
      bottom: 6px;
      min-width: 22px;
      padding: 2px 6px;
      text-align: center;
      font-size: 12px;
      font-weight: 600;
      color: #fff;
      background: rgba(17, 24, 39, 0.65);
      border-radius: 6px;
      transition: background-color 0.2s ease;
    }

    .page-check {
      position: absolute;
      top: 6px;
      right: 6px;
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      background: #0ea5e9;
      border-radius: 50%;
      font-size: 14px;
      animation: check-pop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .page-order-num {
      position: absolute;
      left: 6px;
      bottom: 6px;
      min-width: 24px;
      padding: 3px 8px;
      text-align: center;
      font-size: 13px;
      font-weight: 700;
      color: #fff;
      background: #0ea5e9;
      border-radius: 7px;
      box-shadow: 0 2px 6px rgba(14, 165, 233, 0.4);
    }

    .page-origin-num {
      position: absolute;
      top: 6px;
      left: 6px;
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 600;
      color: #fff;
      background: rgba(17, 24, 39, 0.6);
      border-radius: 8px;
    }

    &.is-selected {
      border-color: #0ea5e9;
      box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.28), 0 8px 20px rgba(14, 165, 233, 0.18);
      animation: card-select-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

      .page-num {
        background: #0ea5e9;
      }
    }

    &.is-dragging {
      opacity: 0.45;
      border-style: dashed;
      border-color: #0ea5e9;
      cursor: grabbing;
    }
  }

  .action-buttons {
    flex-shrink: 0;
    display: flex;
    justify-content: center;
    gap: 16px;
    padding-top: 14px;
    border-top: 1px solid #f0f0f0;

    .el-button {
      padding: 12px 34px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 10px;
      transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;

      &.el-button--primary,
      &.generate-btn {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        border: none;
        box-shadow: 0 6px 16px rgba(14, 165, 233, 0.32);

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 24px rgba(14, 165, 233, 0.42);
          filter: brightness(1.05);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }
      }

      &:not(.el-button--primary):not(.generate-btn) {
        background: #fff;
        border: 1.5px solid #d9dde3;
        color: #4b5563;

        &:hover:not(:disabled) {
          border-color: #7dd3fc;
          color: #0ea5e9;
          background: #fafeff;
          transform: translateY(-1px);
        }
      }
    }
  }
}

// 结果面板
.result-panel {
  padding: 16px 20px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 14px;

  .results-header {
    margin-bottom: 10px;

    .results-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 600;
      color: #065f46;

      .el-icon {
        font-size: 16px;
      }
    }
  }

  .result-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;

    .result-icon {
      color: #10b981;
    }

    .result-name {
      flex: 1;
      min-width: 0;
      font-size: 13px;
      color: #374151;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .el-button {
      padding: 7px 18px;
      font-size: 13px;
      font-weight: 500;
      border-radius: 8px;
      border: none;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
      transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(102, 126, 234, 0.4);
        filter: brightness(1.05);
      }
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes card-select-pop {
  0% {
    transform: scale(0.92);
  }
  60% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes check-pop {
  0% {
    transform: scale(0) rotate(-30deg);
    opacity: 0;
  }
  60% {
    transform: scale(1.25) rotate(8deg);
  }
  100% {
    transform: scale(1) rotate(0);
    opacity: 1;
  }
}

@keyframes card-ripple {
  0% {
    transform: scale(0);
    opacity: 0.6;
  }
  100% {
    transform: scale(9);
    opacity: 0;
  }
}

// 淡入淡出
.file-list-fade-enter-active,
.file-list-fade-leave-active {
  transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-list-fade-enter-from {
  opacity: 0;
  transform: translateY(-16px);
}

.file-list-fade-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>
