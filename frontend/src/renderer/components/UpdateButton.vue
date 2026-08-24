<template>
  <div v-if="visible" class="update-button" :class="status">
    <Button1
      size="small"
      :disabled="status === 'downloading'"
      :title="buttonTitle"
      :aria-label="buttonTitle"
      @click="handleClick"
    >
      <el-icon v-if="status === 'available'"><Bell /></el-icon>
      <el-icon v-else-if="status === 'downloading'"><Loading class="rotating" /></el-icon>
      <el-icon v-else-if="status === 'downloaded'"><RefreshRight /></el-icon>
      <span>{{ label }}</span>
      <span v-if="status === 'available'" class="update-dot"></span>
    </Button1>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Button1 from '../elements/button/button1.vue'

const visible = ref(false)
const status = ref('')        // available | downloading | downloaded
const version = ref('')
const percent = ref(0)

let off = null

onMounted(() => {
  off = window.electronAPI.onUpdateEvent((e) => {
    switch (e.type) {
      case 'available':
        version.value = e.version || ''
        status.value = 'available'
        visible.value = true
        break
      case 'progress':
        status.value = 'downloading'
        percent.value = e.percent ?? 0
        break
      case 'downloaded':
        status.value = 'downloaded'
        break
      case 'error':
        // 启动时的后台自动检查失败保持静默；用户主动操作失败则提示并允许重试
        if (e.silent) return
        window.$toast?.error(`更新失败：${e.message || '未知错误'}`)
        if (status.value === 'downloading') {
          status.value = 'available'
          percent.value = 0
        }
        break
      default:
        break
    }
  })
})

onUnmounted(() => {
  if (off) off()
})

const label = computed(() => {
  if (status.value === 'downloading') return `下载中 ${percent.value}%`
  if (status.value === 'downloaded') return '重启安装'
  return `新版本 v${version.value}`
})

const buttonTitle = computed(() => {
  if (status.value === 'downloading') return '正在下载更新'
  if (status.value === 'downloaded') return '下载完成，点击重启并安装'
  return '发现新版本，点击立即更新'
})

function handleClick() {
  if (status.value === 'available') {
    status.value = 'downloading'
    percent.value = 0
    window.electronAPI.downloadUpdate()
  } else if (status.value === 'downloaded') {
    window.electronAPI.installUpdate()
  }
}
</script>

<style scoped>
.update-button {
  position: relative;
  display: inline-flex;
}

/* 下载中弱化，避免误以为是可点击 */
.update-button.downloading :deep(button) {
  --button_color: #f3f4f6;
  cursor: progress;
}

/* 下载完成：绿色强调，提示用户点击安装 */
.update-button.downloaded :deep(button) {
  --button_outline_color: #16a34a;
  --button_color: #e8f7ee;
}

.update-button.downloaded :deep(.button_top) {
  animation: ready-pulse 1.2s ease-in-out infinite;
}

/* 新版本提示红点 */
.update-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  border: 1.5px solid #fff;
  animation: dot-pulse 1.6s ease-in-out infinite;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes dot-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.35); opacity: 0.75; }
}

@keyframes ready-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.35); }
  50% { box-shadow: 0 0 0 5px rgba(22, 163, 74, 0); }
}
</style>
