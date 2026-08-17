<template>
  <div class="settings-container">
    <div class="settings-content">
      <div class="settings-card">
        <div class="card-header">
          <el-icon :size="24"><Setting /></el-icon>
          <h3>翻译设置</h3>
        </div>
        <div class="card-body">
          <div class="form-item">
            <label class="form-label">
              <span>翻译并发数</span>
              <el-tooltip content="控制同时请求大模型的任务数量，建议 3-8" placement="top">
                <el-icon class="tooltip-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </label>
            <el-input-number
              v-model="form.maxConcurrent"
              :min="1"
              :max="20"
              :step="1"
              class="concurrent-input"
            />
            <span class="form-hint">范围：1 - 20</span>
          </div>

          <div class="form-item">
            <label class="form-label">
              <span>DeepSeek API 密钥</span>
            </label>
            <el-input
              v-model="form.apiKey"
              type="password"
              placeholder="输入 DeepSeek API 密钥"
              show-password
              class="apikey-input"
            />
            <span class="form-hint">密钥将保存在本地，仅用于翻译请求</span>
          </div>
        </div>
      </div>

      <div class="settings-actions">
        <Button1
          class="save-button"
          size="default"
          :class="{ 'is-saving': isSaving }"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          <span>{{ isSaving ? '保存中...' : '保存设置' }}</span>
        </Button1>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Setting, QuestionFilled, Check } from '@element-plus/icons-vue'
import Button1 from '../elements/button/button1.vue'
import { getApiKey, saveApiKey, getMaxConcurrent, saveMaxConcurrent } from '../api/pdf'

const form = ref({
  maxConcurrent: 5,
  apiKey: ''
})

const isSaving = ref(false)

const loadSettings = async () => {
  try {
    const [apiRes, concurrentRes] = await Promise.all([
      getApiKey().catch(() => null),
      getMaxConcurrent().catch(() => null)
    ])

    if (apiRes && apiRes.code === 200 && apiRes.data) {
      form.value.apiKey = apiRes.data.api_key || ''
    }
    if (concurrentRes && concurrentRes.code === 200 && concurrentRes.data) {
      form.value.maxConcurrent = concurrentRes.data.max_concurrent || 5
    }
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

const handleSave = async () => {
  if (isSaving.value) return
  isSaving.value = true

  try {
    await Promise.all([
      saveApiKey(form.value.apiKey),
      saveMaxConcurrent(form.value.maxConcurrent)
    ])
    window.$toast?.success('设置保存成功')
  } catch (error) {
    window.$toast?.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 40px 24px;
  overflow-y: auto;
  background: white;
}

.settings-content {
  width: 100%;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  box-shadow:
    0 4px 20px rgba(17, 24, 39, 0.06),
    0 1px 4px rgba(17, 24, 39, 0.04);
  overflow: hidden;

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 20px 24px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
    color: #111827;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }

    .el-icon {
      color: #4f6bff;
    }
  }

  .card-body {
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .form-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #374151;

    .tooltip-icon {
      color: #9ca3af;
      cursor: help;
      font-size: 14px;
    }
  }

  .form-hint {
    font-size: 12px;
    color: #9ca3af;
  }

  .concurrent-input {
    width: 140px;
  }

  .apikey-input {
    width: 100%;
  }
}

.settings-actions {
  display: flex;
  justify-content: center;

  .save-button {
    --color-background: #4f6bff;
    --color-background-hover: #3d56e0;
    --color-outline: #4f6bff40;
    --color-shadow: #00000040;
    position: relative;
    overflow: visible;
    transition: all 0.5s;

    :deep(.button_top) {
      background: var(--color-background);
      border: none;
      color: #fff;
      box-shadow: 0 0 0.2em 0 var(--color-background);
    }

    &:hover :deep(.button_top) {
      outline: 0.1em solid transparent;
      outline-offset: 0.2em;
      box-shadow: 0 0 1em 0 var(--color-background);
      animation:
        ripple 1s linear infinite,
        colorize 1s infinite;
      transition: 0.5s;
    }

    &:hover :deep(.button_top span) {
      text-shadow: 5px 5px 5px var(--color-shadow);
    }

    &:hover :deep(.button_top .el-icon) {
      filter: drop-shadow(5px 5px 2.5px var(--color-shadow));
    }

    &:active :deep(.button_top) {
      transform: scale(0.95);
    }

    &:active :deep(.button_top span),
    &:active :deep(.button_top .el-icon) {
      text-shadow: none;
      filter: none;
    }

    &.is-saving {
      opacity: 0.7;
      pointer-events: none;
    }
  }
}

@keyframes colorize {
  0% {
    background: var(--color-background);
  }
  50% {
    background: var(--color-background-hover);
  }
  100% {
    background: var(--color-background);
  }
}

@keyframes ripple {
  0% {
    outline: 0em solid transparent;
    outline-offset: -0.1em;
  }
  50% {
    outline: 0.2em solid var(--color-outline);
    outline-offset: 0.2em;
  }
  100% {
    outline: 0.4em solid transparent;
    outline-offset: 0.4em;
  }
}
</style>
