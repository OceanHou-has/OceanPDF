<template>
  <el-dialog
    v-model="dialogVisible"
    width="780px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-header="false"
    :show-close="false"
    class="doc-parser-dialog"
  >
    <div class="dialog-wrapper">
      <!-- 装饰气泡 -->
      <div class="deco-bubbles" aria-hidden="true">
        <span class="bubble b1"></span>
        <span class="bubble b2"></span>
        <span class="bubble b3"></span>
      </div>

      <!-- 自定义标题 -->
      <div class="dialog-header">
        <div class="header-content">
          <div class="mascot">🔧</div>
          <div class="header-text">
            <h2 class="header-title">文档解析服务</h2>
            <p class="header-subtitle">配置外部文档解析API，扩展解析能力</p>
          </div>
        </div>
        <button class="close-btn" @click="handleClose" title="关闭">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- 主体内容 -->
      <div class="dialog-body">
        <!-- 左侧：服务列表 -->
        <div class="service-list">
          <div
            v-for="provider in providers"
            :key="provider.id"
            class="service-item"
            :class="{ active: selectedProvider?.id === provider.id }"
            @click="selectProvider(provider)"
          >
            <span class="service-emoji">{{ provider.emoji }}</span>
            <div class="service-info">
              <div class="service-name">{{ provider.name }}</div>
              <div class="service-status">
                <span class="status-dot" :class="{ configured: isConfigured(provider.id) }"></span>
                <span class="status-text">{{ isConfigured(provider.id) ? '已配置' : '未配置' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：配置表单 -->
        <div class="config-panel" v-if="selectedProvider">
          <div class="config-header">
            <h3 class="config-title">
              <span>{{ selectedProvider.emoji }}</span>
              {{ selectedProvider.name }}
            </h3>
            <p class="config-desc">{{ selectedProvider.description }}</p>
            <a
              v-if="selectedProvider.key_url"
              :href="selectedProvider.key_url"
              target="_blank"
              class="key-link"
            >
              🔑 申请 API Key
            </a>
          </div>

          <div class="config-form">
            <div
              v-for="field in selectedProvider.config_fields"
              :key="field.key"
              class="form-field"
            >
              <label class="field-label">
                {{ field.label }}
                <span v-if="field.required" class="required-mark">*</span>
              </label>
              <el-input
                v-model="formConfig[field.key]"
                :type="field.type === 'password' ? 'password' : 'text'"
                :placeholder="field.placeholder"
                :show-password="field.type === 'password'"
                class="field-input"
              />
            </div>
          </div>

          <!-- 测试结果 -->
          <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
            <span class="result-icon">{{ testResult.success ? '✅' : '❌' }}</span>
            <div class="result-content">
              <div class="result-message">{{ testResult.message }}</div>
              <div class="result-latency" v-if="testResult.latency_ms > 0">
                延迟: {{ testResult.latency_ms }}ms
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="config-actions">
            <button
              class="action-btn test-btn"
              :disabled="isTesting"
              @click="handleTest"
            >
              <el-icon v-if="!isTesting"><Connection /></el-icon>
              <el-icon v-else class="rotating"><Loading /></el-icon>
              <span>{{ isTesting ? '测试中...' : '测试连接' }}</span>
            </button>
            <button
              class="action-btn save-btn"
              :disabled="isSaving"
              @click="handleSave"
            >
              <el-icon v-if="!isSaving"><Check /></el-icon>
              <el-icon v-else class="rotating"><Loading /></el-icon>
              <span>{{ isSaving ? '保存中...' : '保存配置' }}</span>
            </button>
            <button
              v-if="isConfigured(selectedProvider.id)"
              class="action-btn delete-btn"
              @click="handleDelete"
            >
              <el-icon><Delete /></el-icon>
              <span>删除配置</span>
            </button>
          </div>
        </div>

        <!-- 未选择服务时的提示 -->
        <div class="config-panel empty" v-else>
          <div class="empty-hint">
            <span class="empty-icon">👈</span>
            <p>请从左侧选择一个服务进行配置</p>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { Connection, Check, Delete, Loading } from '@element-plus/icons-vue'
import {
  getDocumentParserProviders,
  getDocumentParserConfig,
  saveDocumentParserConfig,
  testDocumentParser,
  deleteDocumentParserConfig
} from '../../api/pdf'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 数据状态
const providers = ref([])
const savedConfig = ref({}) // 已保存的配置（脱敏）
const selectedProvider = ref(null)
const formConfig = reactive({}) // 当前编辑的配置

// 操作状态
const isTesting = ref(false)
const isSaving = ref(false)
const testResult = ref(null)

// 检查某服务是否已配置
function isConfigured(providerId) {
  const config = savedConfig.value[providerId]
  if (!config) return false
  const provider = providers.value.find(p => p.id === providerId)
  if (!provider) return false
  const requiredFields = provider.config_fields.filter(f => f.required).map(f => f.key)
  return requiredFields.every(key => config[key] && config[key].length > 3) // 脱敏后至少有4字符
}

// 选择服务
function selectProvider(provider) {
  selectedProvider.value = provider
  testResult.value = null

  // 清空表单并填充已保存的值
  Object.keys(formConfig).forEach(key => delete formConfig[key])
  const saved = savedConfig.value[provider.id] || {}
  provider.config_fields.forEach(field => {
    // 如果是脱敏值（包含***），则不填充，让用户重新输入
    const val = saved[field.key] || ''
    if (val && !val.includes('***')) {
      formConfig[field.key] = val
    } else {
      formConfig[field.key] = ''
    }
  })
}

// 加载数据
async function loadData() {
  try {
    const [providersRes, configRes] = await Promise.all([
      getDocumentParserProviders(),
      getDocumentParserConfig()
    ])

    if (providersRes?.code === 200 && providersRes.data) {
      providers.value = providersRes.data
    }
    if (configRes?.code === 200 && configRes.data) {
      savedConfig.value = configRes.data
    }
  } catch (error) {
    console.error('加载文档解析配置失败:', error)
    window.$toast?.error('加载配置失败')
  }
}

// 测试连接
async function handleTest() {
  if (!selectedProvider.value) return
  isTesting.value = true
  testResult.value = null

  try {
    // 构建要测试的配置（过滤空值）
    const testConfig = {}
    Object.entries(formConfig).forEach(([key, val]) => {
      if (val) testConfig[key] = val
    })

    const res = await testDocumentParser(selectedProvider.value.id, testConfig)
    testResult.value = res.data || { success: false, message: res.message || '测试失败', latency_ms: 0 }
  } catch (error) {
    testResult.value = { success: false, message: error.message || '测试请求失败', latency_ms: 0 }
  } finally {
    isTesting.value = false
  }
}

// 保存配置
async function handleSave() {
  if (!selectedProvider.value) return

  // 验证必填字段
  const missing = selectedProvider.value.config_fields
    .filter(f => f.required && !formConfig[f.key])
    .map(f => f.label)
  if (missing.length > 0) {
    window.$toast?.warning(`请填写必填项: ${missing.join(', ')}`)
    return
  }

  isSaving.value = true
  try {
    const config = {}
    Object.entries(formConfig).forEach(([key, val]) => {
      if (val) config[key] = val
    })

    const res = await saveDocumentParserConfig(selectedProvider.value.id, config)
    if (res?.code === 200) {
      window.$toast?.success('配置保存成功')
      // 更新已保存配置
      if (res.data?.config) {
        savedConfig.value[selectedProvider.value.id] = res.data.config
      }
    } else {
      window.$toast?.error(res?.message || '保存失败')
    }
  } catch (error) {
    window.$toast?.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    isSaving.value = false
  }
}

// 删除配置
async function handleDelete() {
  if (!selectedProvider.value) return
  try {
    const res = await deleteDocumentParserConfig(selectedProvider.value.id)
    if (res?.code === 200) {
      window.$toast?.success('配置已删除')
      delete savedConfig.value[selectedProvider.value.id]
      // 清空表单
      Object.keys(formConfig).forEach(key => delete formConfig[key])
      testResult.value = null
    }
  } catch (error) {
    window.$toast?.error('删除失败: ' + (error.message || '未知错误'))
  }
}

// 关闭对话框
function handleClose() {
  dialogVisible.value = false
}

// 监听对话框打开
watch(dialogVisible, (val) => {
  if (val) {
    loadData()
    testResult.value = null
  }
})
</script>

<style scoped lang="scss">
:deep(.doc-parser-dialog) {
  .el-dialog {
    border-radius: 20px;
    overflow: hidden;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }
  .el-dialog__body {
    padding: 0;
  }
}

.dialog-wrapper {
  position: relative;
  overflow: hidden;
}

.deco-bubbles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  .bubble {
    position: absolute;
    border-radius: 50%;
    opacity: 0.1;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    animation: float 6s ease-in-out infinite;
    &.b1 { width: 100px; height: 100px; top: -20px; right: -20px; animation-delay: 0s; }
    &.b2 { width: 60px; height: 60px; bottom: 20px; left: -10px; animation-delay: 2s; }
    &.b3 { width: 40px; height: 40px; top: 50%; right: 10%; animation-delay: 4s; }
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  .header-content {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .mascot {
    font-size: 32px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
  }

  .header-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
  }

  .header-subtitle {
    margin: 4px 0 0;
    font-size: 13px;
    opacity: 0.85;
  }

  .close-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: rgba(255,255,255,0.2);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    &:hover { background: rgba(255,255,255,0.35); transform: scale(1.1); }
  }
}

.dialog-body {
  display: flex;
  min-height: 400px;
  padding: 20px;
  gap: 20px;
}

// 左侧服务列表
.service-list {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: 420px;
  padding-right: 8px;

  .service-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    background: white;
    border: 2px solid transparent;

    &:hover {
      border-color: #e2e8f0;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    &.active {
      border-color: #667eea;
      background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .service-emoji {
      font-size: 22px;
      flex-shrink: 0;
    }

    .service-info {
      flex: 1;
      min-width: 0;
    }

    .service-name {
      font-size: 13px;
      font-weight: 600;
      color: #1e293b;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .service-status {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 2px;

      .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #cbd5e1;
        &.configured { background: #22c55e; }
      }

      .status-text {
        font-size: 11px;
        color: #94a3b8;
      }
    }
  }
}

// 右侧配置面板
.config-panel {
  flex: 1;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;

  &.empty {
    align-items: center;
    justify-content: center;
  }

  .empty-hint {
    text-align: center;
    color: #94a3b8;
    .empty-icon { font-size: 40px; display: block; margin-bottom: 12px; }
    p { margin: 0; font-size: 14px; }
  }

  .config-header {
    margin-bottom: 16px;

    .config-title {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .config-desc {
      margin: 6px 0 0;
      font-size: 12px;
      color: #64748b;
    }

    .key-link {
      display: inline-block;
      margin-top: 8px;
      font-size: 12px;
      color: #667eea;
      text-decoration: none;
      &:hover { text-decoration: underline; }
    }
  }

  .config-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
    flex: 1;

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 6px;

      .field-label {
        font-size: 13px;
        font-weight: 500;
        color: #374151;
        .required-mark { color: #ef4444; margin-left: 2px; }
      }

      .field-input {
        :deep(.el-input__wrapper) {
          border-radius: 8px;
          box-shadow: 0 0 0 1px #e2e8f0;
          &:hover { box-shadow: 0 0 0 1px #cbd5e1; }
          &.is-focus { box-shadow: 0 0 0 1px #667eea; }
        }
      }
    }
  }

  // 测试结果
  .test-result {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 14px;
    border-radius: 10px;
    margin-top: 14px;

    &.success {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
    }
    &.error {
      background: #fef2f2;
      border: 1px solid #fecaca;
    }

    .result-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
    .result-content { flex: 1; }
    .result-message { font-size: 13px; color: #1e293b; }
    .result-latency { font-size: 11px; color: #64748b; margin-top: 2px; }
  }

  // 操作按钮
  .config-actions {
    display: flex;
    gap: 10px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f1f5f9;

    .action-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 8px;
      border: none;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      &.test-btn {
        background: #f1f5f9;
        color: #475569;
        &:hover:not(:disabled) { background: #e2e8f0; }
      }

      &.save-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        &:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
      }

      &.delete-btn {
        background: #fef2f2;
        color: #ef4444;
        margin-left: auto;
        &:hover:not(:disabled) { background: #fee2e2; }
      }
    }
  }
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
