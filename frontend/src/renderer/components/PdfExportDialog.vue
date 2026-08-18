<template>
  <el-dialog
    v-model="visible"
    title="选择导出模式"
    width="420px"
    :close-on-click-modal="false"
    :close-on-press-escape="!isDownloading"
    :show-close="!isDownloading"
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
        <el-button :disabled="isDownloading" @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="isDownloading" @click="confirmDownload">
          确认导出
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { exportPDF, getExportDownloadUrl } from '../api/pdf'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  pdfNames: {
    type: Array,
    default: () => []
  },
  useDps: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'finished'])

const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const downloadMode = ref('interleaved')
const isDownloading = ref(false)

watch(() => props.modelValue, isVisible => {
  if (isVisible) {
    downloadMode.value = 'interleaved'
  }
})

const triggerDownload = filename => {
  const downloadLink = document.createElement('a')
  downloadLink.href = getExportDownloadUrl(filename)
  downloadLink.download = filename
  document.body.appendChild(downloadLink)
  downloadLink.click()
  document.body.removeChild(downloadLink)
}

const confirmDownload = async () => {
  const pdfs = props.pdfNames.filter(Boolean)
  if (isDownloading.value || pdfs.length === 0) return

  isDownloading.value = true
  window.$toast?.info(`正在导出 ${pdfs.length} 个PDF...`)

  let successCount = 0
  let failCount = 0

  try {
    for (const pdfName of pdfs) {
      try {
        const result = await exportPDF(pdfName, {
          mode: downloadMode.value,
          use_dps: props.useDps
        })

        if (result.code !== 200 || !result.data) {
          throw new Error(result.message || '导出失败')
        }

        triggerDownload(result.data.filename)
        successCount++
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

    visible.value = false
    emit('finished', { successCount, failCount, mode: downloadMode.value })
  } finally {
    isDownloading.value = false
  }
}
</script>

<style scoped lang="scss">
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
