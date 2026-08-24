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

    <!-- 工具对话框：每个工具使用独立的工作台组件 -->
    <el-dialog
      v-model="dialogVisible"
      :title="activeTool?.name || ''"
      :width="dialogWidth"
      :close-on-click-modal="false"
      :show-close="false"
      destroy-on-close
      class="tool-dialog"
    >
      <template #header="{ close }">
        <div class="tool-dialog-header">
          <div class="header-left">
            <span
              class="header-icon"
              :style="{ backgroundColor: activeTool?.color + '1A', color: activeTool?.color }"
            >
              <el-icon><component :is="activeTool?.icon" /></el-icon>
            </span>
            <span class="header-title">{{ activeTool?.name }}</span>
          </div>
          <button
            class="header-close"
            type="button"
            aria-label="关闭弹窗"
            title="关闭"
            @click="close"
          >
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </template>

      <div class="tool-form">
        <template v-if="activeTool?.id === 'merge'">
          <MergeWorkbench />
        </template>
        <template v-else-if="activeTool?.id === 'split'">
          <SplitWorkbench />
        </template>
        <template v-else-if="activeTool?.id === 'delete'">
          <DeleteWorkbench />
        </template>
        <template v-else-if="activeTool?.id === 'reorder'">
          <ReorderWorkbench />
        </template>
        <template v-else-if="activeTool?.id === 'extract'">
          <ExtractWorkbench />
        </template>
        <template v-else-if="activeTool?.id === 'rotate'">
          <RotateWorkbench />
        </template>
      </div>

    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Document,
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
  Close
} from '@element-plus/icons-vue'
import MergeWorkbench from '../components/MergeWorkbench.vue'
import SplitWorkbench from '../components/SplitWorkbench.vue'
import DeleteWorkbench from '../components/DeleteWorkbench.vue'
import ReorderWorkbench from '../components/ReorderWorkbench.vue'
import ExtractWorkbench from '../components/ExtractWorkbench.vue'
import RotateWorkbench from '../components/RotateWorkbench.vue'

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

// 对话框状态
const dialogVisible = ref(false)
const activeTool = ref(null)

const dialogWidth = computed(() => {
  const widths = {
    merge: '880px',
    split: '860px',
    delete: '860px',
    reorder: '860px',
    extract: '860px',
    rotate: '860px'
  }
  return widths[activeTool.value?.id] || '560px'
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

.tool-form {
  padding: 4px 2px;
}

.tool-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-icon {
    width: 34px;
    height: 34px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    font-size: 18px;
  }

  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .header-close {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    color: #6b7280;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      background: #fef2f2;
      border-color: #fecaca;
      color: #ef4444;
      transform: rotate(90deg);
      box-shadow: 0 3px 10px rgba(239, 68, 68, 0.18);
    }

    &:active {
      transform: scale(0.92);
    }
  }
}
</style>

<!-- 弹窗整体样式（teleport 到 body，使用非 scoped 样式覆盖） -->
<style>
.tool-dialog.el-dialog {
  border-radius: 18px;
  overflow: hidden;
  background: #fbfdff;
  box-shadow:
    0 24px 64px rgba(17, 24, 39, 0.14),
    0 4px 16px rgba(17, 24, 39, 0.08);
}

.tool-dialog .el-dialog__header {
  margin-right: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #eef2f7;
  background: linear-gradient(135deg, #ffffff 0%, #f4f8ff 100%);
}

.tool-dialog .el-dialog__body {
  padding: 20px;
  background: #fbfdff;
  border-radius: 0 0 18px 18px;
}

.tool-dialog .el-dialog__body::-webkit-scrollbar {
  width: 6px;
}

.tool-dialog .el-dialog__body::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 3px;
}
</style>
