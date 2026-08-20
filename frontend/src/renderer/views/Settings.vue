<template>
  <div class="settings-container">
    <div class="settings-layout">
      <!-- 左侧：设置分类 -->
      <div class="settings-nav">
        <div
          class="nav-item"
          :class="{ active: activeSection === 'translation' }"
          @click="activeSection = 'translation'"
        >
          <el-icon :size="18"><Setting /></el-icon>
          <span>翻译设置</span>
        </div>
        <div
          class="nav-item"
          :class="{ active: activeSection === 'parser' }"
          @click="activeSection = 'parser'"
        >
          <el-icon :size="18"><Monitor /></el-icon>
          <span>文档解析服务</span>
          <span class="nav-badge" v-if="configuredCount > 0">{{ configuredCount }}</span>
        </div>
      </div>

      <!-- 右侧：设置内容 -->
      <div class="settings-main">
        <!-- 翻译设置 -->
        <div class="settings-card" v-show="activeSection === 'translation'">
          <div class="card-header">
            <el-icon :size="24"><Setting /></el-icon>
            <h3>翻译设置</h3>
          </div>
          <div class="card-body">
            <!-- 翻译模型选择 -->
            <div class="form-item">
              <label class="form-label">
                <span>翻译模型</span>
              </label>
              <div class="provider-chips">
                <div
                  v-for="p in llmProviders"
                  :key="p.id"
                  class="provider-chip"
                  :class="{ active: form.provider === p.id }"
                  @click="selectLlmProvider(p)"
                >
                  <span class="provider-chip-name">{{ p.name }}</span>
                </div>
              </div>
            </div>

            <div class="form-item">
              <label class="form-label">
                <span>接口地址 (Base URL)</span>
              </label>
              <el-input
                v-model="form.baseUrl"
                placeholder="https://api.example.com/v1"
                class="apikey-input"
              />
              <span class="form-hint">选中厂商会自动填充，也可手动修改为任意 OpenAI 兼容地址</span>
            </div>

            <div class="form-item">
              <label class="form-label">
                <span>模型名称</span>
              </label>
              <el-select
                v-model="form.model"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入模型名称"
                class="model-select"
              >
                <el-option v-for="m in currentLlmModels" :key="m" :label="m" :value="m" />
              </el-select>
            </div>

            <div class="form-item">
              <label class="form-label">
                <span>API 密钥</span>
              </label>
              <div class="api-key-row">
                <el-input
                  v-model="form.apiKey"
                  type="password"
                  :placeholder="currentLlmProvider?.key_placeholder || '输入 API 密钥'"
                  show-password
                  class="apikey-input"
                />
                <button
                  class="test-conn-btn"
                  :disabled="!canTestConn || isTestingConn"
                  :class="{ success: testConnSuccess, error: testConnError }"
                  @click="handleTestConn"
                >
                  <el-icon v-if="isTestingConn" class="rotating"><Loading /></el-icon>
                  <span v-else>{{ testConnSuccess ? '成功' : (testConnError ? '失败' : '测试连接') }}</span>
                </button>
              </div>
              <span class="form-hint" v-if="currentLlmProvider?.key_url">
                <a :href="currentLlmProvider.key_url" target="_blank" class="key-hint-link">前往获取 API Key</a>
              </span>
              <span class="form-hint" v-else>密钥将保存在本地，仅用于翻译请求</span>
              <div v-if="testConnMsg" class="test-msg" :class="testConnSuccess ? 'success' : 'error'">{{ testConnMsg }}</div>
            </div>

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
          </div>

          <div class="card-actions">
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

        <!-- 文档解析服务设置 -->
        <div class="settings-card parser-card" v-show="activeSection === 'parser'">
          <div class="card-header">
            <h3>文档解析服务</h3>
            <span class="header-badge">{{ configuredCount }}/{{ totalServices }} 已配置</span>
          </div>
          <div class="parser-body">
            <!-- 左侧：服务列表 -->
            <div class="parser-service-list">
              <div
                v-for="provider in providers"
                :key="provider.id"
                class="parser-service-item"
                :class="{ active: selectedProvider?.id === provider.id }"
                @click="selectProvider(provider)"
              >
                <div class="parser-service-info">
                  <div class="parser-service-name">{{ provider.name }}</div>
                  <div class="parser-service-status">
                    <span class="status-dot" :class="{ configured: isProviderConfigured(provider.id) }"></span>
                    <span class="status-text">{{ isProviderConfigured(provider.id) ? '已配置' : '未配置' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧：配置表单 -->
            <div class="parser-config-panel" v-if="selectedProvider">
              <div class="parser-config-header">
                <div class="parser-config-title-row">
                  <h4 class="parser-config-title">{{ selectedProvider.name }}</h4>
                  <a
                    v-if="selectedProvider.key_url"
                    :href="selectedProvider.key_url"
                    target="_blank"
                    class="parser-key-btn"
                    title="前往申请 API Key"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                      <polyline points="15 3 21 3 21 9"/>
                      <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                    <span>申请 API Key</span>
                  </a>
                </div>
                <p class="parser-config-desc">{{ selectedProvider.description }}</p>
              </div>

              <div class="parser-config-form">
                <div
                  v-for="field in selectedProvider.config_fields"
                  :key="field.key"
                  class="parser-form-field"
                >
                  <label class="parser-field-label">
                    {{ field.label }}
                    <span v-if="field.required" class="required-mark">*</span>
                  </label>
                  <el-input
                    v-model="parserFormConfig[field.key]"
                    :type="field.type === 'password' ? 'password' : 'text'"
                    :placeholder="field.placeholder"
                    :show-password="field.type === 'password'"
                    class="parser-field-input"
                  />
                </div>
              </div>

              <!-- 测试结果 -->
              <div v-if="parserTestResult" class="parser-test-result" :class="parserTestResult.success ? 'success' : 'error'">
                <span class="result-icon">{{ parserTestResult.success ? '✅' : '❌' }}</span>
                <div class="result-content">
                  <div class="result-message">{{ parserTestResult.message }}</div>
                  <div class="result-latency" v-if="parserTestResult.latency_ms > 0">
                    延迟: {{ parserTestResult.latency_ms }}ms
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="parser-config-actions">
                <button
                  class="parser-action-btn test-btn"
                  :disabled="isTestingParser"
                  @click="handleTestParser"
                >
                  <el-icon v-if="!isTestingParser"><Connection /></el-icon>
                  <el-icon v-else class="rotating"><Loading /></el-icon>
                  <span>{{ isTestingParser ? '测试中...' : '测试连接' }}</span>
                </button>
                <button
                  class="parser-action-btn save-btn"
                  :disabled="isSavingParser"
                  @click="handleSaveParser"
                >
                  <el-icon v-if="!isSavingParser"><Check /></el-icon>
                  <el-icon v-else class="rotating"><Loading /></el-icon>
                  <span>{{ isSavingParser ? '保存中...' : '保存配置' }}</span>
                </button>
                <button
                  v-if="isProviderConfigured(selectedProvider.id)"
                  class="parser-action-btn delete-btn"
                  @click="handleDeleteParser"
                >
                  <el-icon><Delete /></el-icon>
                  <span>删除</span>
                </button>
              </div>
            </div>

            <!-- 未选择服务时的提示 -->
            <div class="parser-config-panel empty" v-else>
              <div class="parser-empty-hint">
                <p>请从左侧选择一个服务进行配置</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Setting, QuestionFilled, Check, Monitor, Connection, Delete, Loading } from '@element-plus/icons-vue'
import Button1 from '../elements/button/button1.vue'
import {
  getApiKey, saveApiKey, getMaxConcurrent, saveMaxConcurrent,
  getDocumentParserProviders, getDocumentParserConfig,
  saveDocumentParserConfig, testDocumentParser, deleteDocumentParserConfig,
  getTranslationProviders, getTranslationModelConfig, saveTranslationModelConfig,
  testTranslationAPI
} from '../api/pdf'

// ========== 翻译设置 ==========
const form = ref({
  provider: 'deepseek',
  baseUrl: 'https://api.deepseek.com',
  model: 'deepseek-v4-flash',
  apiKey: '',
  maxConcurrent: 5
})
const isSaving = ref(false)
const activeSection = ref('translation')

// LLM 厂商列表
const llmProviders = ref([])
const FALLBACK_PROVIDERS = [
  {
    id: 'deepseek', name: 'DeepSeek',
    description: '深度求索，学术翻译性价比高（V4 系列）',
    default_base_url: 'https://api.deepseek.com',
    models: ['deepseek-v4-flash', 'deepseek-v4-pro'], default_model: 'deepseek-v4-flash',
    key_placeholder: '输入 DeepSeek API 密钥（sk-...）',
    key_url: 'https://platform.deepseek.com/api_keys'
  },
  {
    id: 'custom', name: '自定义 (OpenAI 兼容)',
    description: '任意 OpenAI 兼容服务（如 Ollama、OneAPI、中转站等）',
    default_base_url: '', models: [], default_model: '',
    key_placeholder: '输入该服务的 API Key', key_url: ''
  }
]

const currentLlmProvider = computed(() =>
  llmProviders.value.find(p => p.id === form.value.provider) || null
)
const currentLlmModels = computed(() => {
  const list = [...((currentLlmProvider.value && currentLlmProvider.value.models) || [])]
  if (form.value.model && !list.includes(form.value.model)) {
    list.unshift(form.value.model)
  }
  return list
})

function selectLlmProvider(p) {
  form.value.provider = p.id
  form.value.baseUrl = p.default_base_url || ''
  form.value.model = p.default_model || ''
  resetTestConn()
}

// 测试连接
const isTestingConn = ref(false)
const testConnSuccess = ref(false)
const testConnError = ref(false)
const testConnMsg = ref('')
const canTestConn = computed(() =>
  Boolean(form.value.apiKey?.trim() && form.value.baseUrl?.trim() && form.value.model?.trim())
)

function resetTestConn() {
  testConnSuccess.value = false
  testConnError.value = false
  testConnMsg.value = ''
}

async function handleTestConn() {
  if (!canTestConn.value) return
  isTestingConn.value = true
  resetTestConn()
  try {
    // 使用原生 axios 绕过 request 拦截器（拦截器会在 code!==200 时 reject，丢失错误详情）
    const rawAxios = (await import('axios')).default
    const res = await rawAxios.post(
      'http://localhost:8000/api/v1/translation/test',
      null,
      {
        params: {
          api_key: form.value.apiKey,
          provider: form.value.provider,
          base_url: form.value.baseUrl.trim(),
          model: form.value.model.trim()
        },
        timeout: 15000
      }
    )
    const body = res.data
    if (body?.code === 200 && body?.data?.success) {
      testConnSuccess.value = true
      testConnMsg.value = body.data?.message || '连接成功'
    } else {
      testConnError.value = true
      testConnMsg.value = body?.data?.message || body?.message || '连接失败'
    }
  } catch (error) {
    testConnError.value = true
    testConnMsg.value = error.response?.data?.message || error.message || '测试请求失败'
  } finally {
    isTestingConn.value = false
  }
}

const handleSave = async () => {
  if (isSaving.value) return
  isSaving.value = true
  try {
    await Promise.all([
      saveTranslationModelConfig({
        provider: form.value.provider,
        base_url: form.value.baseUrl.trim(),
        model: form.value.model.trim(),
        api_key: form.value.apiKey.trim()
      }),
      saveMaxConcurrent(form.value.maxConcurrent)
    ])
    window.$toast?.success('设置保存成功')
  } catch (error) {
    window.$toast?.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    isSaving.value = false
  }
}

// ========== 文档解析服务设置 ==========
const providers = ref([])
const savedParserConfig = ref({})
const selectedProvider = ref(null)
const parserFormConfig = reactive({})
const isTestingParser = ref(false)
const isSavingParser = ref(false)
const parserTestResult = ref(null)

const configuredCount = computed(() => providers.value.filter(p => isProviderConfigured(p.id)).length)
const totalServices = computed(() => providers.value.length)

function isProviderConfigured(providerId) {
  const config = savedParserConfig.value[providerId]
  if (!config) return false
  const provider = providers.value.find(p => p.id === providerId)
  if (!provider) return false
  const requiredFields = provider.config_fields.filter(f => f.required).map(f => f.key)
  return requiredFields.every(key => config[key] && config[key].length > 3)
}

function selectProvider(provider) {
  selectedProvider.value = provider
  parserTestResult.value = null
  Object.keys(parserFormConfig).forEach(key => delete parserFormConfig[key])
  const saved = savedParserConfig.value[provider.id] || {}
  provider.config_fields.forEach(field => {
    const val = saved[field.key] || ''
    if (val && !val.includes('***')) {
      parserFormConfig[field.key] = val
    } else {
      parserFormConfig[field.key] = ''
    }
  })
}

async function loadParserData() {
  try {
    const [providersRes, configRes] = await Promise.all([
      getDocumentParserProviders(),
      getDocumentParserConfig()
    ])
    if (providersRes?.code === 200 && providersRes.data) {
      providers.value = providersRes.data
    }
    if (configRes?.code === 200 && configRes.data) {
      savedParserConfig.value = configRes.data
    }
  } catch (error) {
    console.error('加载文档解析配置失败:', error)
  }
}

async function handleTestParser() {
  if (!selectedProvider.value) return
  isTestingParser.value = true
  parserTestResult.value = null
  try {
    const testConfig = {}
    Object.entries(parserFormConfig).forEach(([key, val]) => {
      if (val) testConfig[key] = val
    })
    const res = await testDocumentParser(selectedProvider.value.id, testConfig)
    parserTestResult.value = res.data || { success: false, message: res.message || '测试失败', latency_ms: 0 }
  } catch (error) {
    parserTestResult.value = { success: false, message: error.message || '测试请求失败', latency_ms: 0 }
  } finally {
    isTestingParser.value = false
  }
}

async function handleSaveParser() {
  if (!selectedProvider.value) return
  const missing = selectedProvider.value.config_fields
    .filter(f => f.required && !parserFormConfig[f.key])
    .map(f => f.label)
  if (missing.length > 0) {
    window.$toast?.warning(`请填写必填项: ${missing.join(', ')}`)
    return
  }
  isSavingParser.value = true
  try {
    const config = {}
    Object.entries(parserFormConfig).forEach(([key, val]) => {
      if (val) config[key] = val
    })
    const res = await saveDocumentParserConfig(selectedProvider.value.id, config)
    if (res?.code === 200) {
      window.$toast?.success('配置保存成功')
      if (res.data?.config) {
        savedParserConfig.value[selectedProvider.value.id] = res.data.config
      }
    } else {
      window.$toast?.error(res?.message || '保存失败')
    }
  } catch (error) {
    window.$toast?.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    isSavingParser.value = false
  }
}

async function handleDeleteParser() {
  if (!selectedProvider.value) return
  try {
    const res = await deleteDocumentParserConfig(selectedProvider.value.id)
    if (res?.code === 200) {
      window.$toast?.success('配置已删除')
      delete savedParserConfig.value[selectedProvider.value.id]
      Object.keys(parserFormConfig).forEach(key => delete parserFormConfig[key])
      parserTestResult.value = null
    }
  } catch (error) {
    window.$toast?.error('删除失败: ' + (error.message || '未知错误'))
  }
}

// ========== 初始化 ==========
const loadSettings = async () => {
  try {
    // 并行加载所有配置
    const [providersRes, modelConfigRes, concurrentRes] = await Promise.all([
      getTranslationProviders().catch(() => null),
      getTranslationModelConfig().catch(() => null),
      getMaxConcurrent().catch(() => null)
    ])

    // 加载厂商列表
    if (providersRes?.code === 200 && providersRes.data?.length) {
      llmProviders.value = providersRes.data
    } else {
      llmProviders.value = [...FALLBACK_PROVIDERS]
    }

    // 加载已保存的翻译模型配置
    if (modelConfigRes?.code === 200 && modelConfigRes.data) {
      const saved = modelConfigRes.data
      if (saved.provider) form.value.provider = saved.provider
      if (saved.base_url) form.value.baseUrl = saved.base_url
      if (saved.model) {
        // 校验已保存的模型是否仍在厂商的模型列表中，若已下线则使用厂商默认模型
        const provider = llmProviders.value.find(p => p.id === (saved.provider || 'deepseek'))
        if (provider?.models?.length && !provider.models.includes(saved.model)) {
          form.value.model = provider.default_model || ''
        } else {
          form.value.model = saved.model
        }
      }
      if (saved.api_key) form.value.apiKey = saved.api_key
    }

    // 加载并发数
    if (concurrentRes?.code === 200 && concurrentRes.data) {
      form.value.maxConcurrent = concurrentRes.data.max_concurrent || 5
    }

    await loadParserData()
  } catch (error) {
    console.error('加载设置失败:', error)
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
  padding: 32px 24px;
  overflow-y: auto;
  background: white;
}

.settings-layout {
  display: flex;
  gap: 24px;
  max-width: 900px;
  margin: 0 auto;
  min-height: calc(100% - 64px);
}

// 左侧导航
.settings-nav {
  width: 180px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 8px;

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
    font-weight: 500;
    color: #64748b;
    position: relative;

    &:hover {
      background: #f8fafc;
      color: #334155;
    }

    &.active {
      background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
      color: #4f6bff;
      font-weight: 600;

      .el-icon { color: #4f6bff; }
    }

    .nav-badge {
      margin-left: auto;
      font-size: 11px;
      font-weight: 600;
      color: #22c55e;
      background: #f0fdf4;
      padding: 1px 7px;
      border-radius: 10px;
      border: 1px solid #bbf7d0;
    }
  }
}

// 右侧主内容区
.settings-main {
  flex: 1;
  min-width: 0;
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

  .card-actions {
    display: flex;
    justify-content: center;
    padding: 0 24px 24px;
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

  .model-select {
    width: 100%;
  }
}

// 厂商选择
.provider-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .provider-chip {
    display: flex;
    align-items: center;
    padding: 6px 14px;
    border-radius: 8px;
    border: 2px solid #e2e8f0;
    background: #f8fafc;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 13px;
    font-weight: 500;
    color: #475569;

    &:hover {
      border-color: #cbd5e1;
      background: #f1f5f9;
    }

    &.active {
      border-color: #4f6bff;
      background: #f0f4ff;
      color: #4f6bff;
      font-weight: 600;
    }

    .provider-chip-name {
      white-space: nowrap;
    }
  }
}

// API Key 行（输入框 + 测试按钮）
.api-key-row {
  display: flex;
  gap: 10px;
  align-items: center;

  .apikey-input {
    flex: 1;
  }
}

.test-conn-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.success {
    border-color: #22c55e;
    color: #16a34a;
    background: #f0fdf4;
  }

  &.error {
    border-color: #ef4444;
    color: #dc2626;
    background: #fef2f2;
  }
}

.key-hint-link {
  color: #4f6bff;
  text-decoration: none;
  &:hover { text-decoration: underline; }
}

.test-msg {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  &.success { color: #16a34a; background: #f0fdf4; }
  &.error { color: #dc2626; background: #fef2f2; }
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 保存按钮
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

@keyframes colorize {
  0% { background: var(--color-background); }
  50% { background: var(--color-background-hover); }
  100% { background: var(--color-background); }
}

@keyframes ripple {
  0% { outline: 0em solid transparent; outline-offset: -0.1em; }
  50% { outline: 0.2em solid var(--color-outline); outline-offset: 0.2em; }
  100% { outline: 0.4em solid transparent; outline-offset: 0.4em; }
}

// ========== 文档解析服务卡片 ==========
.header-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 10px;
  border-radius: 12px;
}

.parser-body {
  display: flex;
  min-height: 360px;
}

// 左侧服务列表
.parser-service-list {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 12px;
  border-right: 1px solid #f0f0f0;
  background: #fafbfc;
  overflow-y: auto;

  .parser-service-item {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: 2px solid transparent;

    &:hover {
      background: #f1f5f9;
    }

    &.active {
      border-color: #4f6bff;
      background: #f0f4ff;
    }

    .parser-service-info {
      flex: 1;
      min-width: 0;
    }

    .parser-service-name {
      font-size: 13px;
      font-weight: 500;
      color: #334155;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .parser-service-status {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 3px;

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
.parser-config-panel {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;

  &.empty {
    align-items: center;
    justify-content: center;
  }

  .parser-empty-hint {
    text-align: center;
    color: #94a3b8;
    p { margin: 0; font-size: 14px; }
  }

  .parser-config-header {
    .parser-config-title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
  
    .parser-config-title {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
    }
  
    .parser-key-btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      color: #4f6bff;
      background: #f0f4ff;
      border: 1px solid #dbe4ff;
      text-decoration: none;
      transition: all 0.2s;
      white-space: nowrap;
  
      &:hover {
        background: #e0e7ff;
        border-color: #b4c3ff;
        color: #3b52cc;
      }
  
      svg {
        flex-shrink: 0;
      }
    }
  
    .parser-config-desc {
      margin: 8px 0 0;
      font-size: 12px;
      color: #64748b;
    }
  }

  .parser-config-form {
    display: flex;
    flex-direction: column;
    gap: 14px;

    .parser-form-field {
      display: flex;
      flex-direction: column;
      gap: 6px;

      .parser-field-label {
        font-size: 13px;
        font-weight: 500;
        color: #374151;
        .required-mark { color: #ef4444; margin-left: 2px; }
      }

      .parser-field-input {
        :deep(.el-input__wrapper) {
          border-radius: 8px;
          box-shadow: 0 0 0 1px #e2e8f0;
          &:hover { box-shadow: 0 0 0 1px #cbd5e1; }
          &.is-focus { box-shadow: 0 0 0 1px #4f6bff; }
        }
      }
    }
  }

  // 测试结果
  .parser-test-result {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 14px;
    border-radius: 10px;

    &.success {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
    }
    &.error {
      background: #fef2f2;
      border: 1px solid #fecaca;
    }

    .result-icon { font-size: 16px; flex-shrink: 0; }
    .result-content { flex: 1; }
    .result-message { font-size: 13px; color: #1e293b; }
    .result-latency { font-size: 11px; color: #64748b; margin-top: 2px; }
  }

  // 操作按钮
  .parser-config-actions {
    display: flex;
    gap: 10px;
    padding-top: 14px;
    border-top: 1px solid #f1f5f9;

    .parser-action-btn {
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
        background: linear-gradient(135deg, #4f6bff 0%, #6366f1 100%);
        color: white;
        &:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(79, 107, 255, 0.4); }
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
</style>
