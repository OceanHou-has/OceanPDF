<template>
  <div class="split-workbench" :class="{ 'has-files': file }">
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
          <p>上传后可查看每一页缩略图，选中页面分组进行拆分</p>
        </div>
      </div>
    </el-upload>

    <!-- 拆分工作区 -->
    <transition name="file-list-fade">
      <div v-if="file" class="file-panel">
        <div class="panel-header-row">
          <div class="panel-title">
            <el-icon><Tickets /></el-icon>
            <span>拆分设置</span>
          </div>
          <div class="mode-switch">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button value="visual">可视化拆分</el-radio-button>
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

        <!-- ============ 可视化拆分 ============ -->
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
              <span class="group-progress">
                已分组 {{ groupedCount }} / {{ totalPages }} 页
              </span>
              <div class="toolbar-actions">
                <el-button size="small" :disabled="groupedCount === totalPages" @click="selectAll">
                  全选未分组
                </el-button>
                <el-button size="small" :disabled="selected.size === 0" @click="clearSelection">
                  清空选择
                </el-button>
                <el-button size="small" :disabled="totalPages < 2" @click="splitEachPage">
                  每页一个文件
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  :disabled="selected.size === 0"
                  @click="createGroup"
                >
                  新建分组（{{ selected.size }}）
                </el-button>
              </div>
            </div>

            <div v-if="groups.length" class="group-list">
              <div
                v-for="g in groups"
                :key="g.id"
                class="group-chip"
                :style="{ '--group-color': g.color }"
              >
                <span class="group-dot"></span>
                <span class="group-label">{{ g.label }}</span>
                <span class="group-pages" :title="g.pages.join(', ')">
                  {{ groupPagesText(g) }}
                </span>
                <el-button
                  class="group-remove"
                  size="small"
                  text
                  :icon="Close"
                  aria-label="删除分组"
                  @click="removeGroup(g.id)"
                />
              </div>
            </div>

            <p class="visual-hint">
              点击缩略图选择页面（按住 Shift 可连续多选），选中后点击「新建分组」；每组分出一个文件。
            </p>

            <div class="page-grid">
              <div
                v-for="t in thumbnails"
                :key="t.page"
                class="page-card"
                :class="{
                  'is-selected': selected.has(t.page),
                  'is-grouped': groupedMap[t.page]
                }"
                :style="groupedMap[t.page] ? { '--card-color': groupedMap[t.page].color } : {}"
                :title="groupedMap[t.page] ? `已在${groupedMap[t.page].label}中` : `选择第 ${t.page} 页`"
                @click="togglePage(t.page, $event)"
              >
                <img :src="t.image" :alt="`第 ${t.page} 页`" draggable="false" />
                <span class="page-num">{{ t.page }}</span>
                <span v-if="selected.has(t.page)" class="page-check">
                  <el-icon><Check /></el-icon>
                </span>
                <span v-if="groupedMap[t.page]" class="page-group-badge">
                  {{ groupedMap[t.page].label }}
                </span>
              </div>
            </div>
          </template>
        </template>

        <!-- ============ 手动输入模式 ============ -->
        <template v-else>
          <div class="form-field">
            <label class="form-label">拆分方式</label>
            <el-radio-group v-model="splitMode">
              <el-radio value="ranges">按页码范围</el-radio>
              <el-radio value="every">每 N 页拆分</el-radio>
            </el-radio-group>
          </div>
          <div class="form-field">
            <label class="form-label">{{ splitMode === 'ranges' ? '拆分范围' : '每几页一份' }}</label>
            <el-input
              v-if="splitMode === 'ranges'"
              v-model="spec"
              placeholder="如：1-3,4,5-8，每个范围生成一个文件"
            />
            <el-input-number v-else v-model="every" :min="1" :max="999" />
            <span v-if="splitMode === 'ranges'" class="hint">页码从 1 开始，用逗号分隔，支持连续范围</span>
          </div>
        </template>

        <div class="action-buttons">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            @click="handleSplit"
          >
            {{ submitting ? '拆分中...' : '开始拆分' }}
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
          <span>处理完成，共 {{ results.length }} 个文件</span>
        </div>
        <el-button
          class="download-all-btn"
          type="primary"
          size="small"
          :loading="zipping"
          @click="handleDownloadAll"
        >
          <el-icon><Download /></el-icon>
          {{ zipping ? '打包中...' : '一键下载全部' }}
        </el-button>
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
  RefreshLeft,
  Tickets,
  CircleCheckFilled,
  Check,
  Close,
  Download,
  WarningFilled
} from '@element-plus/icons-vue'
import { splitPDF, previewPDF, downloadToolsZip, getToolDownloadUrl } from '../api/tools'

const GROUP_COLORS = ['#4F6BFF', '#7C3AED', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899', '#EF4444']

const uploadRef = ref(null)
const file = ref(null)
const submitting = ref(false)
const zipping = ref(false)
const results = ref([])

// 视图模式：visual 可视化 / manual 手动输入
const viewMode = ref('visual')

// 预览状态
const previewing = ref(false)
const previewError = ref('')
const totalPages = ref(0)
const thumbnails = ref([])

// 分组与选择状态
const groups = ref([])
const selected = ref(new Set())
const lastClicked = ref(0)
let groupSeq = 1

// 手动输入参数
const splitMode = ref('ranges')
const spec = ref('')
const every = ref(1)

// 已分组的页面 -> 分组映射
const groupedMap = computed(() => {
  const map = {}
  for (const g of groups.value) {
    for (const p of g.pages) {
      map[p] = { label: g.label, color: g.color }
    }
  }
  return map
})

const groupedCount = computed(() => Object.keys(groupedMap.value).length)

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
  groups.value = []
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
  groups.value = []
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
  if (groupedMap.value[page]) return

  const s = new Set(selected.value)
  if (event.shiftKey && lastClicked.value) {
    const [a, b] = [Math.min(lastClicked.value, page), Math.max(lastClicked.value, page)]
    for (let p = a; p <= b; p++) {
      if (!groupedMap.value[p]) s.add(p)
    }
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
  const s = new Set()
  for (let p = 1; p <= totalPages.value; p++) {
    if (!groupedMap.value[p]) s.add(p)
  }
  selected.value = s
}

// ---------- 分组 ----------
const createGroup = () => {
  if (selected.value.size === 0) {
    window.$toast?.warning('请先选择页面')
    return
  }
  const pages = [...selected.value].sort((a, b) => a - b)
  groups.value.push({
    id: groupSeq++,
    label: `第 ${groups.value.length + 1} 组`,
    pages,
    color: GROUP_COLORS[(groups.value.length) % GROUP_COLORS.length]
  })
  clearSelection()
}

const removeGroup = (id) => {
  groups.value = groups.value.filter((g) => g.id !== id)
}

const splitEachPage = () => {
  if (totalPages.value < 2) return
  groups.value = Array.from({ length: totalPages.value }, (_, i) => ({
    id: groupSeq++,
    label: `第 ${i + 1} 组`,
    pages: [i + 1],
    color: GROUP_COLORS[i % GROUP_COLORS.length]
  }))
  clearSelection()
  window.$toast?.info('已按每页一个文件设置分组，可点击「开始拆分」')
}

// 页面列表压缩为范围文本，如 [1,2,3,5] -> "1-3,5"
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

const groupPagesText = (g) => {
  const text = toRangeText(g.pages)
  return `${g.pages.length} 页 · ${text}`
}

// ---------- 拆分 ----------
const handleSplit = async () => {
  if (!file.value) {
    window.$toast?.warning('请先选择 PDF 文件')
    return
  }

  let params
  if (viewMode.value === 'visual') {
    if (previewing.value) {
      window.$toast?.warning('页面预览生成中，请稍候')
      return
    }
    if (previewError.value) {
      window.$toast?.warning('预览失败，请使用手动输入模式')
      return
    }
    if (totalPages.value === 0) {
      window.$toast?.warning('未获取到页面信息')
      return
    }

    // 显式分组 + 剩余未分组页面合并为一个文件
    const assigned = new Set()
    const finalGroups = groups.value.map((g) => ({ label: g.label, pages: [...g.pages] }))
    for (const g of finalGroups) {
      for (const p of g.pages) assigned.add(p)
    }
    const unassigned = []
    for (let p = 1; p <= totalPages.value; p++) {
      if (!assigned.has(p)) unassigned.push(p)
    }
    if (unassigned.length) {
      finalGroups.push({ label: '未分组', pages: unassigned })
      window.$toast?.info(`还有 ${unassigned.length} 页未分组，将合并为一个文件`)
    }
    if (!finalGroups.length) {
      window.$toast?.warning('请先创建分组')
      return
    }

    const groupSpec = finalGroups.map((g) => toRangeText(g.pages)).join('|')
    params = { mode: 'ranges', groupSpec }
  } else {
    if (splitMode.value === 'ranges' && !spec.value.trim()) {
      window.$toast?.warning('请输入拆分范围')
      return
    }
    if (splitMode.value === 'every' && (!Number.isInteger(every.value) || every.value < 1)) {
      window.$toast?.warning('每 N 页的 N 必须大于等于 1')
      return
    }
    params = {
      mode: splitMode.value,
      spec: splitMode.value === 'ranges' ? spec.value.trim() : undefined,
      every: splitMode.value === 'every' ? every.value : undefined
    }
  }

  submitting.value = true
  results.value = []
  try {
    const res = await splitPDF(file.value.raw, params)
    if (res && res.code === 200) {
      results.value = res.data?.outputs || []
      window.$toast?.success(`拆分完成，共 ${results.value.length} 个文件`)
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('拆分失败：' + msg)
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

// 一键下载全部（打包为 ZIP）
const handleDownloadAll = async () => {
  if (!results.value.length) return
  if (results.value.length === 1) {
    downloadOutput(results.value[0])
    return
  }
  zipping.value = true
  try {
    const res = await downloadToolsZip(results.value.map((r) => r.filename))
    if (res && res.code === 200) {
      const out = res.data?.outputs?.[0]
      if (out) downloadOutput(out)
      window.$toast?.success('打包完成，开始下载')
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('打包失败：' + msg)
  } finally {
    zipping.value = false
  }
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
.split-workbench {
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
        color: #7c3aed;
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
      color: #7c3aed;
      background: rgba(124, 58, 237, 0.1);
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
      border: 3px solid rgba(124, 58, 237, 0.2);
      border-top-color: #7c3aed;
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

    .group-progress {
      font-size: 13px;
      font-weight: 500;
      color: #374151;
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
          background: #eef1ff;
          border-color: #b8c4ff;
          color: #4f6bff;
          transform: translateY(-1px);
        }

        &:active:not(:disabled) {
          transform: translateY(0);
        }

        &.el-button--primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          color: #fff;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);

          &:hover:not(:disabled) {
            filter: brightness(1.05);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.38);
          }
        }
      }
    }
  }

  // 分组列表
  .group-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .group-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 8px 5px 10px;
      background: rgba(79, 107, 255, 0.06);
      border: 1px solid rgba(79, 107, 255, 0.3);
      border-radius: 10px;
      font-size: 12px;

      .group-dot {
        width: 8px;
        height: 8px;
        flex: 0 0 auto;
        border-radius: 50%;
        background: var(--group-color);
      }

      .group-label {
        font-weight: 600;
        color: #374151;
      }

      .group-pages {
        color: #6b7280;
        max-width: 220px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .group-remove {
        margin-left: 2px;
        color: #9ca3af;

        &:hover {
          color: #ef4444;
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

    // 点击涟漪
    &::after {
      content: '';
      position: absolute;
      left: 50%;
      top: 50%;
      width: 24px;
      height: 24px;
      margin: -12px 0 0 -12px;
      border-radius: 50%;
      background: rgba(79, 107, 255, 0.4);
      opacity: 0;
      pointer-events: none;
    }

    &:active::after {
      animation: card-ripple 0.45s ease-out;
    }

    &:hover {
      border-color: #a5b4fc;
      box-shadow: 0 3px 10px rgba(79, 107, 255, 0.15);
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
      background: #4f6bff;
      border-radius: 50%;
      font-size: 14px;
      animation: check-pop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .page-group-badge {
      position: absolute;
      top: 6px;
      left: 6px;
      max-width: calc(100% - 12px);
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 600;
      color: #fff;
      background: var(--card-color, #4f6bff);
      border-radius: 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &.is-selected {
      border-color: #4f6bff;
      box-shadow: 0 0 0 2px rgba(79, 107, 255, 0.28), 0 8px 20px rgba(79, 107, 255, 0.2);
      animation: card-select-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

      .page-num {
        background: #4f6bff;
      }
    }

    &.is-grouped {
      border-color: var(--card-color);
      cursor: not-allowed;
      opacity: 0.92;
      animation: group-fade-in 0.3s ease;

      &:hover {
        transform: none;
        box-shadow: none;
      }

      .page-group-badge {
        animation: badge-drop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
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
  max-height: 220px;
  overflow-y: auto;

  .results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
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

    .download-all-btn {
      padding: 7px 16px;
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

      .el-icon {
        margin-right: 4px;
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

@keyframes group-fade-in {
  from {
    opacity: 0.5;
    transform: scale(0.95);
  }
  to {
    opacity: 0.92;
    transform: scale(1);
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
