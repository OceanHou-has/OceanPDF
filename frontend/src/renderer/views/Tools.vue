<template>
  <div class="tools-page">
    <div class="tools-inner">
      <!-- 板块：PDF 工具 -->
      <section class="tool-section">
        <div class="section-header">
          <div class="section-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="section-meta">
            <h3 class="section-title">PDF 工具</h3>
            <p class="section-desc">常用的 PDF 页面处理、格式转换与安全优化，一键完成</p>
          </div>
        </div>

        <div v-for="group in toolGroups" :key="group.name" class="tool-group">
          <h4 class="group-title">{{ group.name }}</h4>
          <div class="tool-grid">
            <div
              v-for="tool in group.tools"
              :key="tool.id"
              class="tool-card"
              :class="{ 'is-disabled': !tool.available }"
              :style="{ '--tool-color': tool.color }"
              @click="handleToolClick(tool)"
            >
              <div
                class="tool-icon"
                :style="{ backgroundColor: tool.color + '14', color: tool.color }"
              >
                <el-icon><component :is="tool.icon" /></el-icon>
              </div>
              <div class="tool-info">
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-desc">{{ tool.desc }}</span>
              </div>
              <span class="tool-badge" :class="tool.available ? 'is-ready' : 'is-soon'">
                {{ tool.available ? '可用' : '开发中' }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <p class="tools-footer">更多工具板块（图片处理、格式转换等）即将上线</p>
    </div>

    <!-- 隐藏文件选择框 -->
    <input
      ref="singleInputRef"
      type="file"
      accept=".pdf,application/pdf"
      class="hidden-input"
      @change="onSingleFileChange"
    />
    <input
      ref="mergeInputRef"
      type="file"
      accept=".pdf,application/pdf"
      multiple
      class="hidden-input"
      @change="onMergeFilesChange"
    />

    <!-- 工具对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="activeTool?.name || ''"
      width="560px"
      :close-on-click-modal="false"
      class="tool-dialog"
    >
      <div class="tool-form">
        <!-- 合并 PDF -->
        <template v-if="activeTool?.id === 'merge'">
          <div class="form-field">
            <label class="form-label">选择文件（可多选，按顺序合并）</label>
            <div class="file-picker">
              <el-button type="primary" plain @click="triggerMerge">
                <el-icon style="margin-right: 6px"><FolderOpened /></el-icon>选择 PDF 文件
              </el-button>
              <span class="hint">可多选，选后可用右侧按钮调整顺序</span>
            </div>
          </div>
          <div v-if="mergeFiles.length" class="merge-list">
            <div v-for="(f, i) in mergeFiles" :key="f.name + f.size" class="merge-item">
              <span class="merge-idx">{{ i + 1 }}</span>
              <span class="merge-name" :title="f.name">{{ f.name }}</span>
              <div class="merge-actions">
                <el-button size="small" text :disabled="i === 0" @click="moveMerge(i, -1)">
                  <el-icon><ArrowUp /></el-icon>
                </el-button>
                <el-button size="small" text :disabled="i === mergeFiles.length - 1" @click="moveMerge(i, 1)">
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click="removeMerge(i)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <!-- 单文件工具 -->
        <template v-else-if="singleFileToolIds.includes(activeTool?.id)">
          <div class="form-field">
            <label class="form-label">选择文件</label>
            <div class="file-picker">
              <el-button type="primary" plain @click="triggerSingle">
                <el-icon style="margin-right: 6px"><FolderOpened /></el-icon>选择 PDF 文件
              </el-button>
              <span v-if="singleFile" class="selected-name" :title="singleFile.name">
                <el-icon style="margin-right: 4px"><DocumentChecked /></el-icon>{{ singleFile.name }}
              </span>
            </div>
          </div>

          <!-- 拆分 -->
          <template v-if="activeTool?.id === 'split'">
            <div class="form-field">
              <label class="form-label">拆分方式</label>
              <el-radio-group v-model="form.splitMode">
                <el-radio value="ranges">按页码范围</el-radio>
                <el-radio value="every">每 N 页拆分</el-radio>
              </el-radio-group>
            </div>
            <div class="form-field">
              <label class="form-label">{{ form.splitMode === 'ranges' ? '拆分范围' : '每几页一份' }}</label>
              <el-input
                v-if="form.splitMode === 'ranges'"
                v-model="form.spec"
                placeholder="如：1-3,4,5-8，每个范围生成一个文件"
              />
              <el-input-number v-else v-model="form.every" :min="1" :max="999" />
            </div>
          </template>

          <!-- 提取 / 删除 -->
          <template v-else-if="activeTool?.id === 'extract' || activeTool?.id === 'delete'">
            <div class="form-field">
              <label class="form-label">
                {{ activeTool.id === 'extract' ? '要提取的页码' : '要删除的页码' }}
              </label>
              <el-input
                v-model="form.spec"
                :placeholder="activeTool.id === 'extract' ? '如：1-3,5,7' : '如：2,4-6'"
              />
              <span class="hint">页码从 1 开始，用逗号分隔，支持连续范围</span>
            </div>
          </template>

          <!-- 旋转 -->
          <template v-else-if="activeTool?.id === 'rotate'">
            <div class="form-field">
              <label class="form-label">旋转角度</label>
              <el-radio-group v-model="form.angle">
                <el-radio-button :value="90">顺时针 90°</el-radio-button>
                <el-radio-button :value="180">180°</el-radio-button>
                <el-radio-button :value="270">顺时针 270°</el-radio-button>
              </el-radio-group>
            </div>
            <div class="form-field">
              <el-checkbox v-model="form.rotateAll">全部页面</el-checkbox>
            </div>
            <div v-if="!form.rotateAll" class="form-field">
              <label class="form-label">要旋转的页码</label>
              <el-input v-model="form.rotatePages" placeholder="如：1-3,5" />
            </div>
          </template>

          <!-- 重排 -->
          <template v-else-if="activeTool?.id === 'reorder'">
            <div class="form-field">
              <label class="form-label">新的页面顺序</label>
              <el-input v-model="form.spec" placeholder="如：3,1,2 或 2-4,1（按此顺序重新排列）" />
              <span class="hint">页码从 1 开始，用逗号分隔，支持连续范围</span>
            </div>
          </template>
        </template>
      </div>

      <!-- 处理结果 -->
      <div v-if="results.length" class="tool-results">
        <div class="results-title">处理完成，点击下载：</div>
        <div v-for="r in results" :key="r.filename" class="result-item">
          <el-icon class="result-icon"><Document /></el-icon>
          <span class="result-name" :title="r.filename">{{ r.filename }}</span>
          <el-button type="primary" size="small" @click="downloadOutput(r)">下载</el-button>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" :loading="submitting" @click="submit">{{ submitLabel }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import {
  Document,
  DocumentChecked,
  CopyDocument,
  Tickets,
  Postcard,
  DocumentDelete,
  RefreshRight,
  Sort,
  Picture,
  Camera,
  Memo,
  ScaleToOriginal,
  Lock,
  Unlock,
  Brush,
  InfoFilled,
  FolderOpened,
  ArrowUp,
  ArrowDown,
  Close
} from '@element-plus/icons-vue'
import {
  mergePDFs,
  splitPDF,
  extractPages,
  deletePages,
  rotatePages,
  reorderPages,
  getToolDownloadUrl
} from '../api/tools'

// 每个板块下按用途分组，方便后续扩展新的板块（图片处理、格式转换等）
const toolGroups = [
  {
    name: '页面组织',
    tools: [
      { id: 'merge', name: '合并 PDF', desc: '将多个 PDF 合并为一个文件', icon: CopyDocument, color: '#4F6BFF', available: true },
      { id: 'split', name: '拆分 PDF', desc: '按页码范围拆分成多个文件', icon: Tickets, color: '#7C3AED', available: true },
      { id: 'extract', name: '提取页面', desc: '提取指定页面生成新 PDF', icon: Postcard, color: '#0EA5E9', available: true },
      { id: 'delete', name: '删除页面', desc: '删除 PDF 中的指定页面', icon: DocumentDelete, color: '#EF4444', available: true },
      { id: 'rotate', name: '旋转页面', desc: '旋转页面方向（90/180/270°）', icon: RefreshRight, color: '#F59E0B', available: true },
      { id: 'reorder', name: '页面重排', desc: '调整页面的排列顺序', icon: Sort, color: '#8B5CF6', available: true }
    ]
  },
  {
    name: '格式转换',
    tools: [
      { id: 'pdf2img', name: 'PDF 转图片', desc: '将每页渲染为 PNG/JPG 图片', icon: Picture, color: '#10B981', available: false },
      { id: 'img2pdf', name: '图片转 PDF', desc: '多张图片合成为 PDF 文件', icon: Camera, color: '#06B6D4', available: false },
      { id: 'extract-text', name: '提取文本', desc: '抽取 PDF 中的纯文本内容', icon: Memo, color: '#6366F1', available: false }
    ]
  },
  {
    name: '优化与安全',
    tools: [
      { id: 'compress', name: '压缩 PDF', desc: '减小文件体积，便于分享', icon: ScaleToOriginal, color: '#F97316', available: false },
      { id: 'encrypt', name: '加密 PDF', desc: '为 PDF 设置打开密码', icon: Lock, color: '#64748B', available: false },
      { id: 'decrypt', name: '解密 PDF', desc: '移除 PDF 的密码保护', icon: Unlock, color: '#14B8A6', available: false },
      { id: 'watermark', name: '添加水印', desc: '叠加文字或图片水印', icon: Brush, color: '#EC4899', available: false },
      { id: 'info', name: 'PDF 信息', desc: '查看页数、尺寸与元数据', icon: InfoFilled, color: '#3B82F6', available: false }
    ]
  }
]

const singleFileToolIds = ['split', 'extract', 'delete', 'rotate', 'reorder']

// 对话框状态
const dialogVisible = ref(false)
const activeTool = ref(null)
const submitting = ref(false)
const results = ref([])

// 文件状态
const singleFile = ref(null)
const mergeFiles = ref([])
const singleInputRef = ref(null)
const mergeInputRef = ref(null)

const form = reactive({
  spec: '',
  splitMode: 'ranges',
  every: 1,
  angle: 90,
  rotateAll: true,
  rotatePages: ''
})

const submitLabel = computed(() => {
  const labels = {
    merge: '开始合并',
    split: '开始拆分',
    extract: '开始提取',
    delete: '开始删除',
    rotate: '开始旋转',
    reorder: '开始重排'
  }
  return labels[activeTool.value?.id] || '开始处理'
})

const handleToolClick = (tool) => {
  if (!tool.available) {
    window.$toast?.info(`「${tool.name}」功能开发中，敬请期待`)
    return
  }
  openTool(tool)
}

const openTool = (tool) => {
  activeTool.value = tool
  dialogVisible.value = true
  results.value = []
  singleFile.value = null
  mergeFiles.value = []
  Object.assign(form, {
    spec: '',
    splitMode: 'ranges',
    every: 1,
    angle: 90,
    rotateAll: true,
    rotatePages: ''
  })
}

const triggerSingle = () => singleInputRef.value?.click()
const triggerMerge = () => mergeInputRef.value?.click()

const onSingleFileChange = (e) => {
  const f = e.target.files?.[0]
  if (f) singleFile.value = f
  e.target.value = ''
}

const onMergeFilesChange = (e) => {
  const files = Array.from(e.target.files || [])
  for (const f of files) {
    if (!mergeFiles.value.some((x) => x.name === f.name && x.size === f.size)) {
      mergeFiles.value.push(f)
    }
  }
  e.target.value = ''
}

const removeMerge = (i) => mergeFiles.value.splice(i, 1)
const moveMerge = (i, dir) => {
  const j = i + dir
  if (j < 0 || j >= mergeFiles.value.length) return
  const arr = mergeFiles.value
  const tmp = arr[i]
  arr[i] = arr[j]
  arr[j] = tmp
}

const submit = async () => {
  const tool = activeTool.value
  if (!tool) return

  if (tool.id === 'merge') {
    if (mergeFiles.value.length < 2) {
      window.$toast?.warning('请至少选择 2 个 PDF 文件')
      return
    }
  } else {
    if (!singleFile.value) {
      window.$toast?.warning('请先选择 PDF 文件')
      return
    }
    if (['extract', 'delete', 'reorder'].includes(tool.id) && !form.spec.trim()) {
      window.$toast?.warning('请输入页码')
      return
    }
    if (tool.id === 'split' && form.splitMode === 'ranges' && !form.spec.trim()) {
      window.$toast?.warning('请输入拆分范围')
      return
    }
    if (tool.id === 'rotate' && !form.rotateAll && !form.rotatePages.trim()) {
      window.$toast?.warning('请输入要旋转的页码')
      return
    }
  }

  submitting.value = true
  results.value = []
  try {
    let res
    switch (tool.id) {
      case 'merge':
        res = await mergePDFs(mergeFiles.value)
        break
      case 'split':
        res = await splitPDF(singleFile.value, {
          mode: form.splitMode,
          spec: form.splitMode === 'ranges' ? form.spec : undefined,
          every: form.splitMode === 'every' ? form.every : undefined
        })
        break
      case 'extract':
        res = await extractPages(singleFile.value, form.spec)
        break
      case 'delete':
        res = await deletePages(singleFile.value, form.spec)
        break
      case 'rotate':
        res = await rotatePages(singleFile.value, {
          angle: form.angle,
          pages: form.rotateAll ? undefined : form.rotatePages
        })
        break
      case 'reorder':
        res = await reorderPages(singleFile.value, form.spec)
        break
    }
    if (res && res.code === 200) {
      results.value = res.data.outputs || []
      window.$toast?.success(`处理完成，共 ${results.value.length} 个文件`)
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    window.$toast?.error('处理失败：' + msg)
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
</script>

<style scoped lang="scss">
.tools-page {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 24px 24px;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: #cfd4dd;
    border-radius: 3px;

    &:hover {
      background: #b9c0cc;
    }
  }
}

.tools-inner {
  max-width: 1080px;
  margin: 0 auto;
}

.tool-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 14px;

  .section-icon {
    width: 48px;
    height: 48px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(79, 107, 255, 0.14), rgba(79, 107, 255, 0.06));
    color: #4F6BFF;

    .el-icon {
      font-size: 26px;
    }
  }

  .section-meta {
    .section-title {
      font-size: 20px;
      font-weight: 600;
      color: #111827;
      margin: 0 0 4px 0;
    }

    .section-desc {
      font-size: 13px;
      color: #6B7280;
      margin: 0;
    }
  }
}

.tool-group {
  .group-title {
    font-size: 13px;
    font-weight: 600;
    color: #9CA3AF;
    letter-spacing: 0.5px;
    margin: 0 0 12px 0;
    padding-left: 2px;
  }

  .tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 14px;
  }
}

.tool-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 14px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, opacity 0.18s ease;
  box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);

  &:hover {
    transform: translateY(-2px);
    border-color: transparent;
    box-shadow:
      0 10px 28px rgba(17, 24, 39, 0.09),
      0 0 0 1px var(--tool-color);
  }

  &:active {
    transform: translateY(0);
  }

  &.is-disabled {
    opacity: 0.62;

    &:hover {
      transform: none;
      box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
      border-color: #E5E7EB;
    }
  }

  .tool-icon {
    width: 44px;
    height: 44px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;

    .el-icon {
      font-size: 22px;
    }
  }

  .tool-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;

    .tool-name {
      font-size: 15px;
      font-weight: 600;
      color: #111827;
      line-height: 1.2;
    }

    .tool-desc {
      font-size: 12px;
      color: #9CA3AF;
      line-height: 1.35;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .tool-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;

    &.is-ready {
      background: #D1FAE5;
      color: #065F46;
    }

    &.is-soon {
      background: #FEF3C7;
      color: #B45309;
    }
  }
}

.tools-footer {
  margin: 28px 0 8px;
  text-align: center;
  font-size: 12px;
  color: #C0C5CE;
}

.hidden-input {
  display: none;
}

// 对话框内容
.tool-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 4px 2px;

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
      color: #9CA3AF;
    }
  }

  .file-picker {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;

    .hint {
      font-size: 12px;
      color: #9CA3AF;
    }

    .selected-name {
      display: inline-flex;
      align-items: center;
      font-size: 13px;
      color: #374151;
      background: #F3F4F6;
      padding: 6px 12px;
      border-radius: 8px;
      max-width: 320px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .merge-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 240px;
    overflow-y: auto;

    .merge-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      background: #F9FAFB;
      border: 1px solid #E5E7EB;
      border-radius: 10px;

      .merge-idx {
        width: 22px;
        height: 22px;
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        color: #4F6BFF;
        background: rgba(79, 107, 255, 0.1);
        border-radius: 6px;
      }

      .merge-name {
        flex: 1;
        min-width: 0;
        font-size: 13px;
        color: #374151;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .merge-actions {
        display: flex;
        align-items: center;
        flex: 0 0 auto;
      }
    }
  }
}

.tool-results {
  margin-top: 18px;
  padding: 14px;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 12px;

  .results-title {
    font-size: 13px;
    font-weight: 600;
    color: #065F46;
    margin-bottom: 10px;
  }

  .result-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;

    .result-icon {
      color: #10B981;
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
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
