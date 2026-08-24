<template>
  <div class="merge-workbench" :class="{ 'has-files': mergeFiles.length > 0 }">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      class="upload-area"
      :class="{ 'compact-mode': mergeFiles.length > 0 }"
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      :multiple="true"
      accept=".pdf,application/pdf"
    >
      <div class="upload-content">
        <el-icon class="upload-icon">
          <UploadFilled />
        </el-icon>
        <div v-if="mergeFiles.length === 0" class="upload-text">
          <p class="main-text">拖拽 PDF 文件到此处</p>
          <p class="sub-text">或</p>
          <el-button type="primary" size="large" class="upload-btn">
            选择文件上传
          </el-button>
        </div>
        <div v-else class="upload-text compact">
          <el-button type="primary" class="upload-btn-compact">
            <el-icon><Plus /></el-icon>
            继续添加文件
          </el-button>
        </div>
        <div v-if="mergeFiles.length === 0" class="upload-tips">
          <p>支持格式：PDF（可多选）</p>
          <p>至少选择 2 个文件进行合并</p>
        </div>
      </div>
    </el-upload>

    <!-- 文件列表：拖拽调整合并顺序 -->
    <transition name="file-list-fade">
      <div v-if="mergeFiles.length > 0" class="file-panel">
        <div class="panel-header-row">
          <div class="panel-title">
            <el-icon><Sort /></el-icon>
            <span>合并顺序</span>
          </div>
          <span class="panel-hint">拖动卡片调整顺序</span>
          <span class="file-count">{{ mergeFiles.length }} 个文件</span>
        </div>

        <div class="merge-list">
          <div
            v-for="(item, index) in mergeFiles"
            :key="item.key"
            class="merge-item"
            :class="{
              'is-dragging': dragIndex === index,
              'is-drop-target': dropIndex === index && dragIndex !== index
            }"
            draggable="true"
            @dragstart="onDragStart($event, index)"
            @dragover.prevent="onDragOver(index)"
            @drop.prevent="onDrop(index)"
            @dragend="onDragEnd"
          >
            <span class="drag-handle">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="9" cy="6" r="1.6" />
                <circle cx="15" cy="6" r="1.6" />
                <circle cx="9" cy="12" r="1.6" />
                <circle cx="15" cy="12" r="1.6" />
                <circle cx="9" cy="18" r="1.6" />
                <circle cx="15" cy="18" r="1.6" />
              </svg>
            </span>
            <span class="merge-idx">{{ index + 1 }}</span>
            <el-icon class="file-icon"><Document /></el-icon>
            <div class="file-details">
              <p class="file-name" :title="item.name">{{ item.name }}</p>
              <p class="file-size">{{ formatFileSize(item.size) }}</p>
            </div>
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              :disabled="submitting"
              aria-label="移除文件"
              @click="removeFile(index)"
            />
          </div>
        </div>

        <p v-if="mergeFiles.length < 2" class="merge-hint">至少需要 2 个文件才能合并</p>

        <div class="action-buttons">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="mergeFiles.length < 2"
            @click="handleMerge"
          >
            {{ submitting ? '合并中...' : '开始合并' }}
          </el-button>
          <el-button size="large" :disabled="submitting" @click="clearAll">
            清空列表
          </el-button>
        </div>
      </div>
    </transition>

    <!-- 处理结果 -->
    <div v-if="results.length" class="result-panel">
      <div class="results-title">
        <el-icon><CircleCheckFilled /></el-icon>
        <span>处理完成，点击下载：</span>
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
  Delete,
  Plus,
  Sort,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { mergePDFs, getToolDownloadUrl } from '../api/tools'

const uploadRef = ref(null)
const mergeFiles = ref([])
const submitting = ref(false)
const results = ref([])

// 拖拽排序状态
const dragIndex = ref(-1)
const dropIndex = ref(-1)

// ---------- 文件选择 ----------
const handleFileChange = (file) => {
  const raw = file?.raw
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

  const key = `${raw.name}__${raw.size}__${raw.lastModified}`
  if (mergeFiles.value.some((it) => it.key === key)) {
    window.$toast?.warning('已在列表中：' + raw.name)
    return
  }

  mergeFiles.value.push({
    key,
    name: raw.name,
    size: raw.size,
    file: raw
  })
}

const removeFile = (index) => {
  mergeFiles.value.splice(index, 1)
  results.value = []
  resetDrag()
  if (mergeFiles.value.length === 0) {
    uploadRef.value?.clearFiles()
  }
}

const clearAll = () => {
  mergeFiles.value = []
  results.value = []
  resetDrag()
  uploadRef.value?.clearFiles()
}

// ---------- 拖拽排序 ----------
const resetDrag = () => {
  dragIndex.value = -1
  dropIndex.value = -1
}

const onDragStart = (e, index) => {
  dragIndex.value = index
  dropIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

const onDragOver = (index) => {
  if (dragIndex.value === index) return
  dropIndex.value = index
}

const onDrop = (index) => {
  const from = dragIndex.value
  if (from === index) {
    resetDrag()
    return
  }
  const arr = mergeFiles.value.slice()
  const [moved] = arr.splice(from, 1)
  arr.splice(index, 0, moved)
  mergeFiles.value = arr
  results.value = []
  resetDrag()
}

const onDragEnd = () => {
  resetDrag()
}

// ---------- 合并 ----------
const handleMerge = async () => {
  if (mergeFiles.value.length < 2) {
    window.$toast?.warning('请至少选择 2 个 PDF 文件')
    return
  }

  submitting.value = true
  results.value = []
  try {
    const files = mergeFiles.value.map((it) => it.file)
    const res = await mergePDFs(files)
    if (res && res.code === 200) {
      results.value = res.data?.outputs || []
      window.$toast?.success(`合并完成，共 ${results.value.length} 个文件`)
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('合并失败：' + msg)
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
.merge-workbench {
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
    min-height: 260px;
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

  // 有文件后的紧凑模式
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
  padding: clamp(20px, 4vh, 36px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  .upload-icon {
    font-size: clamp(44px, 7vh, 64px);
    color: #667eea;
    margin-bottom: clamp(12px, 2.5vh, 20px);
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
    margin-top: clamp(14px, 3vh, 24px);
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

// 文件面板
.file-panel {
  padding: clamp(16px, 3vh, 22px);
  background: white;
  border-radius: 14px;
  border: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  .panel-header-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 15px;
      font-weight: 600;
      color: #1a1a1a;

      .el-icon {
        color: #4f6bff;
        font-size: 18px;
      }
    }

    .panel-hint {
      font-size: 12px;
      color: #9ca3af;
    }

    .file-count {
      margin-left: auto;
      font-size: 12px;
      font-weight: 500;
      color: #4f6bff;
      background: rgba(79, 107, 255, 0.1);
      padding: 4px 10px;
      border-radius: 12px;
    }
  }

  .merge-list {
    max-height: 280px;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 6px;
    margin-bottom: 14px;

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

  .merge-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 12px;
    margin-bottom: 12px;
    cursor: grab;
    transition: background-color 0.2s ease, border-color 0.2s ease, opacity 0.2s ease, transform 0.2s ease;

    &:hover {
      background: #f3f5ff;
      border-color: rgba(79, 107, 255, 0.35);
    }

    &:active {
      cursor: grabbing;
    }

    &.is-dragging {
      opacity: 0.45;
    }

    &.is-drop-target {
      border-color: #4f6bff;
      background: #eef1ff;
      box-shadow: 0 0 0 2px rgba(79, 107, 255, 0.15);
    }

    .drag-handle {
      flex: 0 0 auto;
      color: #c0c4cc;
      display: flex;
      align-items: center;

      svg {
        display: block;
      }
    }

    .merge-idx {
      width: 26px;
      height: 26px;
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 600;
      color: #4f6bff;
      background: rgba(79, 107, 255, 0.12);
      border-radius: 8px;
    }

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

  .merge-hint {
    font-size: 12px;
    color: #e6a23c;
    margin: -6px 0 12px;
  }

  .action-buttons {
    flex-shrink: 0;
    display: flex;
    justify-content: center;
    gap: 16px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;

    .el-button {
      padding: 12px 34px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 10px;
      transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;

      &.el-button--primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.32);

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 24px rgba(102, 126, 234, 0.42);
          filter: brightness(1.05);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }
      }

      &:not(.el-button--primary) {
        background: #fff;
        border: 1.5px solid #d9dde3;
        color: #4b5563;

        &:hover:not(:disabled) {
          border-color: #b8c4ff;
          color: #4f6bff;
          background: #fafbff;
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

  .results-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #065f46;
    margin-bottom: 10px;

    .el-icon {
      font-size: 16px;
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

// 文件列表淡入淡出
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
