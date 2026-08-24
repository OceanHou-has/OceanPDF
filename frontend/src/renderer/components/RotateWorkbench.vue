<template>
  <div class="rotate-workbench" :class="{ 'has-files': file }">
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
          <p>单击页面直接旋转 90°，也可以多选或全部批量旋转</p>
        </div>
      </div>
    </el-upload>

    <!-- 旋转工作区 -->
    <transition name="file-list-fade">
      <div v-if="file" class="file-panel">
        <div class="panel-header-row">
          <div class="panel-title">
            <el-icon><RefreshRight /></el-icon>
            <span>旋转设置</span>
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

        <template v-else>
          <div class="visual-toolbar">
            <div class="angle-group">
              <span class="angle-label">旋转角度</span>
              <el-radio-group v-model="angle" size="small">
                <el-radio-button :value="90">90°</el-radio-button>
                <el-radio-button :value="180">180°</el-radio-button>
                <el-radio-button :value="270">270°</el-radio-button>
              </el-radio-group>
            </div>
            <div class="toolbar-actions">
              <el-button size="small" :disabled="selected.size === 0" @click="rotateSelected">
                旋转选中页（{{ selected.size }}）
              </el-button>
              <el-button size="small" @click="rotateAll">旋转全部</el-button>
              <el-button size="small" :disabled="!hasRotations" @click="clearRotations">
                清空旋转
              </el-button>
            </div>
          </div>

          <p class="visual-hint">
            已旋转 {{ rotatedCount }} 页 · 单击页面旋转 90°（可连续点击），Shift+单击 多选后点「旋转选中页」
          </p>

          <div class="page-grid">
            <div
              v-for="t in pages"
              :key="t.page"
              class="page-card"
              :class="{ 'is-selected': selected.has(t.page), 'is-rotated': rotationMap[t.page] }"
              :title="`第 ${t.page} 页${rotationMap[t.page] ? `（已旋转 ${rotationMap[t.page]}°）` : ''}`"
              @click="handleCardClick(t.page, $event)"
            >
              <div class="page-img-wrap" :style="wrapStyle(t.page)">
                <img
                  class="rot-img"
                  :class="{ 'is-flat': isFlat(t.page) }"
                  :style="{ '--rot': rotationMap[t.page] ? rotationMap[t.page] + 'deg' : '0deg' }"
                  :src="t.image"
                  :alt="`第 ${t.page} 页`"
                  draggable="false"
                />
              </div>
              <span class="page-num">{{ t.page }}</span>
              <span v-if="selected.has(t.page)" class="page-check">
                <el-icon><Check /></el-icon>
              </span>
              <span v-if="rotationMap[t.page]" class="page-rot-badge">
                {{ rotationMap[t.page] }}°
              </span>
            </div>
          </div>
        </template>

        <div class="action-buttons">
          <el-button
            class="generate-btn"
            type="primary"
            size="large"
            :loading="submitting"
            @click="handleGenerate"
          >
            {{ submitting ? '生成中...' : '生成并下载' }}
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
import { computed, ref } from 'vue'
import {
  UploadFilled,
  Document,
  RefreshRight,
  RefreshLeft,
  CircleCheckFilled,
  Check,
  WarningFilled
} from '@element-plus/icons-vue'
import { rotatePages, previewPDF, getToolDownloadUrl } from '../api/tools'

const uploadRef = ref(null)
const file = ref(null)
const submitting = ref(false)
const results = ref([])

// 预览状态
const previewing = ref(false)
const previewError = ref('')
const totalPages = ref(0)
const pages = ref([])

// 每页已应用的旋转角度（相对于原图）
const rotationMap = ref({})

// 批量选择状态
const selected = ref(new Set())

// 批量旋转角度
const angle = ref(90)

const hasRotations = computed(() =>
  Object.values(rotationMap.value).some((v) => v > 0)
)

const rotatedCount = computed(() =>
  Object.values(rotationMap.value).filter((v) => v > 0).length
)

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
  pages.value = []
  rotationMap.value = {}
  selected.value = new Set()
  uploadRef.value?.clearFiles()
}

// ---------- 预览生成 ----------
const loadPreview = async () => {
  if (!file.value) return
  previewing.value = true
  previewError.value = ''
  totalPages.value = 0
  pages.value = []
  rotationMap.value = {}
  selected.value = new Set()
  results.value = []

  try {
    const res = await previewPDF(file.value.raw)
    if (res && res.code === 200) {
      const data = res.data || {}
      totalPages.value = data.total_pages || 0
      pages.value = data.pages || []
      window.$toast?.success(`已生成 ${totalPages.value} 页预览`)
    }
  } catch (e) {
    previewError.value = e?.response?.data?.detail || e?.message || '预览生成失败'
    window.$toast?.error(previewError.value)
  } finally {
    previewing.value = false
  }
}

// ---------- 旋转 ----------
const addRotation = (page, delta) => {
  const map = { ...rotationMap.value }
  const next = ((map[page] || 0) + delta) % 360
  if (next === 0) delete map[page]
  else map[page] = next
  rotationMap.value = map
}

const handleCardClick = (page, event) => {
  if (event.shiftKey) {
    const s = new Set(selected.value)
    if (s.has(page)) s.delete(page)
    else s.add(page)
    selected.value = s
    return
  }
  addRotation(page, 90)
}

const rotateSelected = () => {
  if (selected.value.size === 0) {
    window.$toast?.warning('请先选择页面（Shift+单击）')
    return
  }
  const map = { ...rotationMap.value }
  for (const p of selected.value) {
    const next = ((map[p] || 0) + angle.value) % 360
    if (next === 0) delete map[p]
    else map[p] = next
  }
  rotationMap.value = map
  selected.value = new Set()
}

const rotateAll = () => {
  const map = { ...rotationMap.value }
  for (let p = 1; p <= totalPages.value; p++) {
    const next = ((map[p] || 0) + angle.value) % 360
    if (next === 0) delete map[p]
    else map[p] = next
  }
  rotationMap.value = map
  selected.value = new Set()
}

const clearRotations = () => {
  rotationMap.value = {}
}

// ---------- 缩略图旋转样式 ----------
const pageInfo = computed(() => {
  const map = {}
  for (const t of pages.value) {
    map[t.page] = t
  }
  return map
})

const isFlat = (page) => {
  const rot = rotationMap.value[page] || 0
  return rot % 180 === 0
}

const wrapStyle = (page) => {
  const rot = rotationMap.value[page] || 0
  const t = pageInfo.value[page]
  let ar
  if (t?.width && t?.height) {
    ar = rot % 180 === 0 ? t.width / t.height : t.height / t.width
  } else {
    ar = rot % 180 === 0 ? 0.707 : 1.414
  }
  return { '--rot-ar': ar }
}

// ---------- 生成 ----------
const handleGenerate = async () => {
  if (!file.value) {
    window.$toast?.warning('请先选择 PDF 文件')
    return
  }
  if (!hasRotations.value) {
    window.$toast?.info('尚未旋转任何页面')
    return
  }

  const rotationMapSpec = Object.entries(rotationMap.value)
    .filter(([, v]) => v > 0)
    .map(([p, v]) => `${p}:${v}`)
    .join(',')

  submitting.value = true
  results.value = []
  try {
    const res = await rotatePages(file.value.raw, {
      angle: angle.value,
      rotationMap: rotationMapSpec
    })
    if (res && res.code === 200) {
      results.value = res.data?.outputs || []
      window.$toast?.success('旋转完成')
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('旋转失败：' + msg)
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
.rotate-workbench {
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
        color: #f59e0b;
        font-size: 18px;
      }
    }

    .file-count {
      margin-left: auto;
      font-size: 12px;
      font-weight: 500;
      color: #f59e0b;
      background: rgba(245, 158, 11, 0.12);
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
      border: 3px solid rgba(245, 158, 11, 0.2);
      border-top-color: #f59e0b;
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

    .angle-group {
      display: flex;
      align-items: center;
      gap: 10px;

      .angle-label {
        font-size: 13px;
        font-weight: 500;
        color: #374151;
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
          background: #fffbeb;
          border-color: #fde68a;
          color: #f59e0b;
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
    max-height: 340px;
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
      background: rgba(245, 158, 11, 0.4);
      opacity: 0;
      pointer-events: none;
    }

    &:active::after {
      animation: card-ripple 0.45s ease-out;
    }

    &:hover {
      border-color: #fcd34d;
      box-shadow: 0 3px 10px rgba(245, 158, 11, 0.15);
      transform: translateY(-1px);
    }

    .page-img-wrap {
      position: relative;
      width: 100%;
      aspect-ratio: var(--rot-ar, 0.707);
      overflow: hidden;
      background: #f3f4f6;
    }

    .rot-img {
      position: absolute;
      left: 50%;
      top: 50%;
      transition: transform 0.3s ease;
      pointer-events: none;

      &.is-flat {
        width: 100%;
        height: 100%;
        transform: translate(-50%, -50%) rotate(var(--rot, 0deg));
      }

      &:not(.is-flat) {
        width: calc(100% / var(--rot-ar, 1));
        height: calc(100% * var(--rot-ar, 1));
        transform: translate(-50%, -50%) rotate(var(--rot, 0deg));
      }
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
      background: #f59e0b;
      border-radius: 50%;
      font-size: 14px;
      animation: check-pop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .page-rot-badge {
      position: absolute;
      top: 6px;
      right: 6px;
      min-width: 36px;
      padding: 2px 8px;
      text-align: center;
      font-size: 11px;
      font-weight: 700;
      color: #b45309;
      background: #fef3c7;
      border: 1px solid #fde68a;
      border-radius: 8px;
      animation: badge-drop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    &.is-selected {
      border-color: #f59e0b;
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.28), 0 8px 20px rgba(245, 158, 11, 0.18);
      animation: card-select-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

      .page-num {
        background: #f59e0b;
      }
    }

    &.is-rotated {
      border-color: #fcd34d;
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

      &.generate-btn {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        border: none;
        color: #fff;
        box-shadow: 0 6px 16px rgba(245, 158, 11, 0.32);

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 24px rgba(245, 158, 11, 0.42);
          filter: brightness(1.05);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }
      }

      &:not(.generate-btn) {
        background: #fff;
        border: 1.5px solid #d9dde3;
        color: #4b5563;

        &:hover:not(:disabled) {
          border-color: #fcd34d;
          color: #f59e0b;
          background: #fffdf5;
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

@keyframes badge-drop {
  from {
    transform: translateY(-10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
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
