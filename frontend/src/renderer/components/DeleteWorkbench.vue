<template>
  <div class="delete-workbench" :class="{ 'has-files': file }">
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
          <p>上传后可查看每一页缩略图，选中要删除的页面</p>
        </div>
      </div>
    </el-upload>

    <!-- 删除工作区 -->
    <transition name="file-list-fade">
      <div v-if="file" class="file-panel">
        <div class="panel-header-row">
          <div class="panel-title">
            <el-icon><DocumentDelete /></el-icon>
            <span>删除设置</span>
          </div>
          <div class="mode-switch">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button value="visual">可视化删除</el-radio-button>
              <el-radio-button value="manual">手动输入</el-radio-button>
            </el-radio-group>
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

        <!-- ============ 可视化删除 ============ -->
        <template v-if="viewMode === 'visual'">
          <div v-if="previewing" class="preview-loading">
            <div class="spinner"></div>
            <p>正在生成页面预览，请稍候...</p>
          </div>

          <div v-else-if="previewError" class="preview-error">
            <el-icon><WarningFilled /></el-icon>
            <p>{{ previewError }}</p>
            <div class="preview-error-actions">
              <el-button size="small" @click="loadPreview">重试</el-button>
              <el-button size="small" type="primary" plain @click="viewMode = 'manual'">
                改用手动输入
              </el-button>
            </div>
          </div>

          <template v-else>
            <div class="visual-toolbar">
              <span class="delete-progress">
                <span class="danger-count">已选 {{ selected.size }} 页</span>
                <span>删除后剩余 {{ totalPages - selected.size }} / {{ totalPages }} 页</span>
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

            <p class="visual-hint">点击缩略图选择要删除的页面（按住 Shift 可连续多选）</p>

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
                  <el-icon><Close /></el-icon>
                </span>
              </div>
            </div>
          </template>
        </template>

        <!-- ============ 手动输入模式 ============ -->
        <template v-else>
          <div class="form-field">
            <label class="form-label">要删除的页码</label>
            <el-input v-model="spec" placeholder="如：2,4-6" />
            <span class="hint">页码从 1 开始，用逗号分隔，支持连续范围</span>
          </div>
        </template>

        <div class="action-buttons">
          <el-button
            class="delete-btn"
            type="danger"
            size="large"
            :loading="submitting"
            @click="handleDelete"
          >
            {{ submitting ? '删除中...' : '开始删除' }}
          </el-button>
          <el-button size="large" :disabled="submitting" @click="clearFile">
            清空
          </el-button>
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
import { ref } from 'vue'
import {
  UploadFilled,
  Document,
  DocumentDelete,
  RefreshLeft,
  CircleCheckFilled,
  Close,
  WarningFilled
} from '@element-plus/icons-vue'
import { deletePages, previewPDF, getToolDownloadUrl } from '../api/tools'

const uploadRef = ref(null)
const file = ref(null)
const submitting = ref(false)
const results = ref([])

// 视图模式：visual 可视化 / manual 手动输入
const viewMode = ref('visual')

// 预览状态
const previewing = ref(false)
const previewError = ref('')
const totalPages = ref(0)
const thumbnails = ref([])

// 选择状态
const selected = ref(new Set())
const lastClicked = ref(0)

// 手动输入参数
const spec = ref('')

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
    viewMode.value = 'manual'
  } finally {
    previewing.value = false
  }
}

// ---------- 页面选择 ----------
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

// 页面列表压缩为范围文本，如 [2,4,5,6] -> "2,4-6"
const toRangeText = (pages) => {
  const arr = [...pages].sort((a, b) => a - b)
  const parts = []
  let start = arr[0]
  let prev = arr[0]
  for (let i = 1; i <= arr.length; i++) {
    const cur = arr[i]
    if (cur === prev + 1) {
      prev = cur
      continue
    }
    parts.push(start === prev ? `${start}` : `${start}-${prev}`)
    start = cur
    prev = cur
  }
  return parts.join(',')
}

// ---------- 删除 ----------
const handleDelete = async () => {
  if (!file.value) {
    window.$toast?.warning('请先选择 PDF 文件')
    return
  }

  let deleteSpec
  if (viewMode.value === 'visual') {
    if (previewing.value) {
      window.$toast?.warning('页面预览生成中，请稍候')
      return
    }
    if (previewError.value) {
      window.$toast?.warning('预览失败，请使用手动输入模式')
      return
    }
    if (selected.value.size === 0) {
      window.$toast?.warning('请先选择要删除的页面')
      return
    }
    if (selected.value.size === totalPages.value) {
      window.$toast?.warning('不能删除全部页面')
      return
    }
    deleteSpec = toRangeText([...selected.value])
  } else {
    if (!spec.value.trim()) {
      window.$toast?.warning('请输入要删除的页码')
      return
    }
    deleteSpec = spec.value.trim()
  }

  submitting.value = true
  results.value = []
  try {
    const res = await deletePages(file.value.raw, deleteSpec)
    if (res && res.code === 200) {
      results.value = res.data?.outputs || []
      window.$toast?.success('删除完成')
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('删除失败：' + msg)
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
.delete-workbench {
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
        color: #ef4444;
        font-size: 18px;
      }
    }

    .mode-switch {
      :deep(.el-radio-button__inner) {
        padding: 6px 12px;
      }
    }

    .file-count {
      margin-left: auto;
      font-size: 12px;
      font-weight: 500;
      color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
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
      border: 3px solid rgba(239, 68, 68, 0.2);
      border-top-color: #ef4444;
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

    .delete-progress {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      font-weight: 500;
      color: #374151;

      .danger-count {
        color: #ef4444;
        font-weight: 600;
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
          background: #fef2f2;
          border-color: #fecaca;
          color: #ef4444;
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
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
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
      background: rgba(239, 68, 68, 0.4);
      opacity: 0;
      pointer-events: none;
    }

    &:active::after {
      animation: card-ripple 0.45s ease-out;
    }

    &:hover {
      border-color: #fca5a5;
      box-shadow: 0 3px 10px rgba(239, 68, 68, 0.15);
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
      background: #ef4444;
      border-radius: 50%;
      font-size: 14px;
      animation: check-pop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    &.is-selected {
      border-color: #ef4444;
      box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.28), 0 8px 20px rgba(239, 68, 68, 0.18);
      animation: card-select-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

      .page-num {
        background: #ef4444;
      }
    }
  }

  // 手动输入表单
  .form-field {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .form-label {
      font-size: 14px;
      font-weight: 500;
      color: #374151;
    }

    .hint {
      font-size: 12px;
      color: #9ca3af;
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

      &.delete-btn {
        background: linear-gradient(135deg, #f87171 0%, #dc2626 100%);
        border: none;
        color: #fff;
        box-shadow: 0 6px 16px rgba(239, 68, 68, 0.32);

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 24px rgba(239, 68, 68, 0.42);
          filter: brightness(1.05);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }
      }

      &:not(.delete-btn) {
        background: #fff;
        border: 1.5px solid #d9dde3;
        color: #4b5563;

        &:hover:not(:disabled) {
          border-color: #fca5a5;
          color: #ef4444;
          background: #fefafa;
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
