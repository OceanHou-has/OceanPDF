<template>
  <el-dialog
    v-model="dialogVisible"
    width="680px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-header="false"
    :show-close="false"
    class="translation-config-dialog"
  >
    <div class="cartoon-wrap">
      <!-- 装饰气泡 -->
      <div class="deco-bubbles" aria-hidden="true">
        <span class="bubble b1"></span>
        <span class="bubble b2"></span>
        <span class="bubble b3"></span>
        <span class="bubble b4"></span>
      </div>

      <!-- 自定义标题 -->
      <div class="dialog-header">
        <div class="header-content">
          <div class="header-text">
            <h2 class="header-title">翻译配置</h2>
            <p class="header-subtitle">配置翻译模型、语言与解析参数</p>
          </div>
        </div>
        <button class="close-btn" @click="handleCancel" title="关闭">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="config-card">
        <div class="config-container">
          <!-- 解析模式选择 -->
          <div class="config-section section-blue">
            <div class="section-header">
              <h3 class="section-title">解析模式</h3>
              <span class="badge badge-required">必选</span>
            </div>
            <div class="mode-cards">
              <div
                class="mode-card"
                :class="{ 'active': !config.useDps }"
                @click="config.useDps = false"
              >
                <div class="mode-info">
                  <div class="mode-title">
                    <span>Python 解析</span>
                    <span class="tag tag-green">推荐</span>
                  </div>
                  <p class="mode-desc">使用人工标注结果，翻译质量更高，适合精细化翻译</p>
                </div>
                <div class="mode-check">
                  <svg v-if="!config.useDps" width="16" height="16" viewBox="0 0 20 20" fill="none">
                    <path d="M16.667 5L7.5 14.167 3.333 10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>

              <div
                class="mode-card"
                :class="{ 'active': config.useDps }"
                @click="config.useDps = true"
              >
                <div class="mode-info">
                  <div class="mode-title">
                    <span>DPS/OCR 解析</span>
                    <span class="tag tag-orange">快速</span>
                  </div>
                  <p class="mode-desc">直接使用OCR识别结果，无需人工标注，快速开始</p>
                </div>
                <div class="mode-check">
                  <svg v-if="config.useDps" width="16" height="16" viewBox="0 0 20 20" fill="none">
                    <path d="M16.667 5L7.5 14.167 3.333 10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- 语言设置 -->
          <div class="config-section section-green">
            <div class="section-header">
              <h3 class="section-title">语言设置</h3>
            </div>
            <div class="lang-container">
              <div class="lang-item">
                <label class="lang-label">源语言</label>
                <el-select v-model="config.sourceLang" placeholder="选择源语言" class="lang-select">
                  <el-option label="🇬🇧 英语 (English)" value="en" />
                  <el-option label="🇨🇳 中文" value="zh" />
                  <el-option label="🇯🇵 日语 (日本語)" value="ja" />
                  <el-option label="🇰🇷 韩语 (한국어)" value="ko" />
                  <el-option label="🇫🇷 法语 (Français)" value="fr" />
                  <el-option label="🇩🇪 德语 (Deutsch)" value="de" />
                  <el-option label="🇪🇸 西班牙语 (Español)" value="es" />
                </el-select>
              </div>

              <div class="swap-fish" aria-hidden="true">
                <span class="fish">🐟</span>
                <span class="fish-trail">〰</span>
              </div>

              <div class="lang-item">
                <label class="lang-label">目标语言</label>
                <el-select v-model="config.targetLang" placeholder="选择目标语言" class="lang-select">
                  <el-option label="🇨🇳 中文简体" value="zh-CN" />
                  <el-option label="🇭🇰 中文繁体" value="zh-TW" />
                  <el-option label="🇬🇧 英语 (English)" value="en" />
                  <el-option label="🇯🇵 日语 (日本語)" value="ja" />
                  <el-option label="🇰🇷 韩语 (한국어)" value="ko" />
                </el-select>
              </div>
            </div>
          </div>

          <!-- 高级选项 -->
          <div class="config-section section-purple">
            <div class="section-header">
              <h3 class="section-title">高级选项</h3>
              <span class="badge badge-optional">可选</span>
            </div>
            <div class="option-card">
              <div class="option-main">
                <div class="option-info">
                  <div class="option-text">
                    <label class="option-label">聚合标题</label>
                    <p class="option-description">将相邻的同类型标题合并为一个翻译任务</p>
                  </div>
                </div>
                <el-switch v-model="config.aggregateTitles" size="large" class="cartoon-switch" />
              </div>
              <div v-if="config.aggregateTitles" class="option-warning">
                <span>不推荐开启，可能影响翻译质量</span>
              </div>
            </div>
          </div>

          <!-- 并发控制 -->
          <div class="config-section section-orange">
            <div class="section-header">
              <h3 class="section-title">并发控制</h3>
              <span class="badge badge-optional">可选</span>
            </div>
            <div class="option-card">
              <div class="option-main">
                <div class="option-info">
                  <div class="option-text">
                    <label class="option-label">翻译并发数</label>
                    <p class="option-description">控制同时请求大模型的任务数量，建议 3-5，过高可能触发限流</p>
                  </div>
                </div>
                <el-input-number v-model="config.maxConcurrent" :min="1" :max="20" :step="1" class="concurrency-input" />
              </div>
            </div>
          </div>

          <!-- 翻译模型配置 -->
          <div class="config-section section-gray">
            <div class="section-header">
              <h3 class="section-title">翻译模型</h3>
              <span class="badge badge-required">必选</span>
            </div>

            <!-- 厂商选择 -->
            <div class="provider-grid">
              <div
                v-for="p in providers"
                :key="p.id"
                class="provider-chip"
                :class="{ active: config.provider === p.id }"
                @click="selectProvider(p)"
              >
                <span class="provider-name">{{ p.name }}</span>
              </div>
            </div>
            <p v-if="currentProvider && currentProvider.description" class="provider-desc">
              {{ currentProvider.description }}
            </p>

            <!-- 模型与接口地址 -->
            <div class="model-row">
              <div class="model-field">
                <label class="model-label">模型</label>
                <el-select
                  v-model="config.model"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择或输入模型名称"
                  class="full-width"
                >
                  <el-option v-for="m in currentModels" :key="m" :label="m" :value="m" />
                </el-select>
              </div>
              <div class="model-field">
                <label class="model-label">接口地址 (Base URL)</label>
                <el-input
                  v-model="config.baseUrl"
                  placeholder="https://api.example.com/v1（选中厂商会自动填充，可手动修改）"
                  class="full-width"
                  @input="handleApiKeyChange"
                />
              </div>
            </div>
          </div>

          <!-- API密钥配置 -->
          <div class="config-section section-pink">
            <div class="section-header">
              <h3 class="section-title">API密钥</h3>
              <span class="badge badge-required">必填</span>
            </div>
            <div class="api-key-wrapper">
              <el-input
                v-model="config.apiKey"
                type="password"
                :placeholder="apiKeyPlaceholder"
                show-password
                class="api-key-input"
                @input="handleApiKeyChange"
              />
              <button
                class="test-btn"
                @click="handleTestApiKey"
                :disabled="!config.apiKey || !canTestApi || testing"
                :class="{ 'success': testSuccess, 'error': testError }"
              >
                <span class="loading-spinner-small" v-if="testing"></span>
                <template v-else>{{ testSuccess ? '测试成功' : (testError ? '测试失败' : '测试连接') }}</template>
              </button>
            </div>
            <a
              v-if="currentProvider && currentProvider.key_url"
              class="key-link"
              :href="currentProvider.key_url"
              target="_blank"
              rel="noopener"
            >
              去获取 {{ currentProvider.name }} API Key
            </a>
            <p v-if="testSuccess" class="test-message success">
              API Key 有效，已保存到本地
            </p>
            <p v-if="testError" class="test-message error">
              {{ testErrorMessage }}
            </p>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="footer-btn btn-cancel" @click="handleCancel">
            取消
          </button>
          <button
            class="footer-btn btn-translate"
            :disabled="!canStartTranslate"
            @click="handleStartTranslate"
          >
            开始翻译
          </button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  pdfName: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'dialog-closed'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 配置数据
const config = ref({
  useDps: false, // false=Python解析, true=DPS/OCR
  sourceLang: 'en',
  targetLang: 'zh-CN',
  aggregateTitles: false,
  provider: 'deepseek',
  baseUrl: 'https://api.deepseek.com',
  model: 'deepseek-v4-flash',
  apiKey: '',
  maxConcurrent: 5
})

// 大模型厂商列表（优先从后端加载，失败时使用内置兑底，需与后端 llm_providers.py 保持一致）
const FALLBACK_PROVIDERS = [
  {
    id: 'deepseek', name: 'DeepSeek', emoji: '🐳',
    description: '深度求索，学术翻译性价比高（V4 系列）',
    default_base_url: 'https://api.deepseek.com',
    models: ['deepseek-v4-flash', 'deepseek-v4-pro'], default_model: 'deepseek-v4-flash',
    key_placeholder: '输入 DeepSeek API 密钥（sk-...）',
    key_url: 'https://platform.deepseek.com/api_keys'
  },
  {
    id: 'custom', name: '自定义 (OpenAI 兼容)', emoji: '🛠️',
    description: '任意 OpenAI 兼容服务（如 Ollama、OneAPI、中转站等）',
    default_base_url: '', models: [], default_model: '',
    key_placeholder: '输入该服务的 API Key（本地服务可填任意值）', key_url: ''
  }
]
const providers = ref([...FALLBACK_PROVIDERS])

const currentProvider = computed(() =>
  providers.value.find(p => p.id === config.value.provider) || null
)

const currentModels = computed(() => {
  const list = [...((currentProvider.value && currentProvider.value.models) || [])]
  // 保证当前已选/自定义模型也在下拉列表中
  if (config.value.model && !list.includes(config.value.model)) {
    list.unshift(config.value.model)
  }
  return list
})

const apiKeyPlaceholder = computed(() => {
  if (currentProvider.value && currentProvider.value.key_placeholder) {
    return currentProvider.value.key_placeholder
  }
  return '输入 API 密钥'
})

// 测试连接需要：API Key + 接口地址 + 模型
const canTestApi = computed(() =>
  Boolean(config.value.baseUrl?.trim() && config.value.model?.trim())
)

const testing = ref(false)
const testSuccess = ref(false)
const testError = ref(false)
const testErrorMessage = ref('')

// 与开始翻译所需参数保持一致，统一驱动按钮的可用状态和视觉样式。
const canStartTranslate = computed(() => {
  const apiKey = config.value.apiKey?.trim()
  const pdfName = props.pdfName?.trim()
  const baseUrl = config.value.baseUrl?.trim()
  const model = config.value.model?.trim()
  const maxConcurrent = Number(config.value.maxConcurrent)

  return Boolean(
    pdfName &&
    apiKey &&
    baseUrl &&
    model &&
    config.value.sourceLang &&
    config.value.targetLang &&
    Number.isFinite(maxConcurrent) &&
    maxConcurrent >= 1 &&
    maxConcurrent <= 20
  )
})

// 选择厂商：自动填充默认 base_url 与模型
const selectProvider = (provider) => {
  if (config.value.provider === provider.id) return
  config.value.provider = provider.id
  config.value.baseUrl = provider.default_base_url || ''
  config.value.model = provider.default_model || ''
  // 切换厂商后重置测试状态
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''
}

// 加载厂商列表（返回是否从后端成功加载，供模型校验判断能否信任列表）
const providersFromBackend = ref(false)
const loadProviders = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/v1/translation/providers')
    if (response.data.code === 200 && Array.isArray(response.data.data) && response.data.data.length) {
      providers.value = response.data.data
      providersFromBackend.value = true
      return
    }
  } catch (error) {
    console.log('加载厂商列表失败，使用内置列表')
  }
  providersFromBackend.value = false
}

// 监听对话框打开状态：重置配置后加载已保存的模型配置
watch(() => props.modelValue, async (newValue, oldValue) => {
  if (newValue) {
    resetConfig()
    await Promise.all([loadProviders(), loadSavedModelConfig()])
    // 加载完成后校验模型有效性，若已下线则回退到厂商默认
    validateCurrentModel()
  } else if (oldValue === true && newValue === false) {
    emit('dialog-closed')
  }
})

// 初始化：首次挂载且已打开时加载
onMounted(async () => {
  if (props.modelValue) {
    resetConfig()
    await Promise.all([loadProviders(), loadSavedModelConfig()])
    validateCurrentModel()
  }
})

// 重置配置为默认值
const resetConfig = () => {
  config.value = {
    useDps: false,
    sourceLang: 'en',
    targetLang: 'zh-CN',
    aggregateTitles: false,
    provider: 'deepseek',
    baseUrl: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
    apiKey: '',
    maxConcurrent: 5
  }
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''
}

// 校验当前模型是否在厂商模型列表中，若已下线则回退到厂商默认
// 注意：厂商列表未从后端成功加载时不可信，跳过校验避免误把用户已保存的模型回退丢失
const validateCurrentModel = () => {
  if (!providersFromBackend.value) return
  const provider = providers.value.find(p => p.id === config.value.provider)
  if (provider?.models?.length && config.value.model && !provider.models.includes(config.value.model)) {
    console.log(`模型 ${config.value.model} 已不在 ${provider.name} 列表中，回退到默认 ${provider.default_model}`)
    config.value.model = provider.default_model || ''
  }
}

// 加载已保存的翻译模型配置（厂商/base_url/模型/API Key/并发数）
const loadSavedModelConfig = async () => {
  try {
    const [modelRes, concurrentRes] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/v1/translation/config/model-config'),
      axios.get('http://127.0.0.1:8000/api/v1/translation/config/max-concurrent').catch(() => null)
    ])
    if (modelRes.data.code === 200 && modelRes.data.data) {
      const saved = modelRes.data.data
      if (saved.provider) config.value.provider = saved.provider
      if (saved.base_url) config.value.baseUrl = saved.base_url
      if (saved.model) config.value.model = saved.model
      if (saved.api_key) config.value.apiKey = saved.api_key
      console.log('加载已保存的翻译模型配置:', saved.provider, saved.model, saved.masked_key)
    }
    if (concurrentRes?.data?.code === 200 && concurrentRes.data.data) {
      const mc = concurrentRes.data.data.max_concurrent
      if (mc && mc >= 1 && mc <= 20) config.value.maxConcurrent = mc
      console.log('加载已保存的并发数:', mc)
    }
  } catch (error) {
    console.log('未找到已保存的翻译配置')
  }
}

// 配置变化时重置测试状态
const handleApiKeyChange = () => {
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''
}

// 测试 API 连接
const handleTestApiKey = async () => {
  if (!config.value.apiKey || !config.value.apiKey.trim()) {
    window.$toast?.warning('请先输入 API Key')
    return
  }
  if (!config.value.baseUrl?.trim()) {
    window.$toast?.warning('请填写接口地址 (Base URL)')
    return
  }
  if (!config.value.model?.trim()) {
    window.$toast?.warning('请选择或输入模型名称')
    return
  }

  testing.value = true
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''

  try {
    // 测试连接（携带厂商/接口地址/模型）
    const response = await axios.post(
      'http://127.0.0.1:8000/api/v1/translation/test',
      null,
      {
        params: {
          api_key: config.value.apiKey,
          provider: config.value.provider,
          base_url: config.value.baseUrl.trim(),
          model: config.value.model.trim()
        }
      }
    )

    if (response.data.code === 200 && response.data.data.success) {
      testSuccess.value = true
      window.$toast?.success('API Key 验证成功')

      // 测试成功后保存完整模型配置
      await saveModelConfig()
    } else {
      testError.value = true
      testErrorMessage.value = response.data.message || 'API Key 无效'
      window.$toast?.error(testErrorMessage.value)
    }
  } catch (error) {
    testError.value = true
    testErrorMessage.value = error.response?.data?.detail || error.message || '测试失败'
    window.$toast?.error('测试失败：' + testErrorMessage.value)
  } finally {
    testing.value = false
  }
}

// 保存翻译模型配置到后端
const saveModelConfig = async () => {
  try {
    const response = await axios.post(
      'http://127.0.0.1:8000/api/v1/translation/config/model-config',
      {
        provider: config.value.provider,
        base_url: config.value.baseUrl.trim(),
        model: config.value.model.trim(),
        api_key: config.value.apiKey.trim()
      }
    )

    if (response.data.code === 200) {
      console.log('翻译模型配置已保存:', response.data.data)
    }
  } catch (error) {
    console.error('保存翻译模型配置失败:', error)
  }
}

// 取消
const handleCancel = () => {
  dialogVisible.value = false
}

const handleStartTranslate = async () => {
  if (!config.value.apiKey || !config.value.apiKey.trim()) {
    window.$toast?.warning('请先输入 API 密钥')
    return
  }
  if (!config.value.model?.trim()) {
    window.$toast?.warning('请选择或输入翻译模型')
    return
  }
  if (!config.value.baseUrl?.trim()) {
    window.$toast?.warning('请填写接口地址 (Base URL)')
    return
  }

  if (!props.pdfName) {
    window.$toast?.error('缺少PDF名称')
    return
  }

  // 开始前静默保存一次配置（无需测试成功也可保存）
  saveModelConfig()

  // 关闭对话框并跳转到翻译执行页面
  dialogVisible.value = false

  router.push({
    path: '/translation',
    query: {
      pdfName: props.pdfName,
      apiKey: config.value.apiKey,
      useDps: config.value.useDps,
      sourceLang: config.value.sourceLang,
      targetLang: config.value.targetLang,
      aggregateTitles: config.value.aggregateTitles,
      maxConcurrent: config.value.maxConcurrent,
      provider: config.value.provider,
      baseUrl: config.value.baseUrl.trim(),
      model: config.value.model.trim()
    }
  })
}

onUnmounted(() => {
  // 清理逻辑（如需）
})
</script>

<style scoped lang="scss">
// ===== 卡通海洋风配色 =====
$ink: #3d5a73;          // 主文字色
$sub-ink: #8aa2b8;      // 次要文字
$blue: #58b6f0;         // 主蓝
$blue-dark: #2e8bc7;    // 深蓝（立体阴影）
$green: #6fce93;
$orange: #ffb45d;
$pink: #ff9eb5;
$purple: #b3a4f3;
$yellow: #ffd97d;
$line: #e8f1f8;         // 浅描边

.cartoon-wrap {
  position: relative;
  background:
    radial-gradient(circle at 20% 15%, #eaf7ff 0 2px, transparent 2px),
    radial-gradient(circle at 70% 40%, #eaf7ff 0 2px, transparent 2px),
    radial-gradient(circle at 45% 80%, #eaf7ff 0 2px, transparent 2px),
    linear-gradient(180deg, #fdfeff 0%, #f4fbff 100%);
  background-size: 90px 90px, 120px 120px, 100px 100px, 100% 100%;
  border-radius: 28px;
  border: 3px solid #cfe9fb;
  box-shadow: 0 12px 0 rgba(88, 182, 240, 0.16), 0 24px 60px rgba(46, 90, 122, 0.25);
  overflow: hidden;
  animation: pop-in 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes pop-in {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(16px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

// 装饰气泡
.deco-bubbles {
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 0;

  .bubble {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(160, 216, 248, 0.35));
    border: 2px solid rgba(140, 205, 245, 0.4);
    animation: bubble-float 5s ease-in-out infinite;
  }

  .b1 { width: 18px; height: 18px; right: 90px; top: 96px; animation-delay: 0s; }
  .b2 { width: 10px; height: 10px; right: 60px; top: 150px; animation-delay: 1.2s; }
  .b3 { width: 14px; height: 14px; left: 34px; bottom: 80px; animation-delay: 0.6s; }
  .b4 { width: 8px; height: 8px; left: 70px; bottom: 140px; animation-delay: 2s; }
}

@keyframes bubble-float {
  0%, 100% { transform: translateY(0); opacity: 0.8; }
  50% { transform: translateY(-10px); opacity: 1; }
}

// ===== 头部 =====
.dialog-header {
  position: relative;
  background: linear-gradient(135deg, #6fc7f5 0%, #4aa9ec 100%);
  padding: 18px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;

  &::after {
    // 卡通波浪底边
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 14px;
    background:
      radial-gradient(circle at 10px -4px, transparent 0 12px, #fdfeff 12px) 0 0 / 28px 14px repeat-x;
  }

  .header-deco {
    position: absolute;
    inset: 0;
    pointer-events: none;

    .star {
      position: absolute;
      color: rgba(255, 255, 255, 0.9);
      animation: twinkle 2.2s ease-in-out infinite;
    }

    .s1 { right: 130px; top: 12px; font-size: 14px; }
    .s2 { right: 70px; top: 34px; font-size: 10px; animation-delay: 0.8s; }

    .cloud {
      position: absolute;
      right: 160px;
      bottom: 10px;
      font-size: 20px;
      opacity: 0.75;
      animation: cloud-drift 7s ease-in-out infinite;
    }
  }

  .header-content {
    display: flex;
    align-items: center;
    gap: 14px;
    position: relative;
    z-index: 1;
  }

  .mascot {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.95);
    border: 3px solid #ffffff;
    box-shadow: 0 4px 0 rgba(46, 139, 199, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    animation: mascot-bounce 2.6s ease-in-out infinite;
  }

  .header-text {
    .header-title {
      font-size: 19px;
      font-weight: 800;
      color: #ffffff;
      margin: 0;
      letter-spacing: 2px;
      text-shadow: 0 2px 0 rgba(46, 139, 199, 0.45);
    }

    .header-subtitle {
      margin: 3px 0 0;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.9);
      letter-spacing: 0.5px;
    }
  }

  .close-btn {
    position: relative;
    z-index: 1;
    background: rgba(255, 255, 255, 0.25);
    border: 2px solid rgba(255, 255, 255, 0.6);
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #ffffff;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

    &:hover {
      background: #ffffff;
      color: #4aa9ec;
      transform: rotate(90deg) scale(1.1);
    }

    &:active {
      transform: rotate(90deg) scale(0.9);
    }
  }
}

@keyframes mascot-bounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  30% { transform: translateY(-5px) rotate(-6deg); }
  60% { transform: translateY(1px) rotate(4deg); }
}

@keyframes twinkle {
  0%, 100% { opacity: 0.4; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.2); }
}

@keyframes cloud-drift {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(12px); }
}

// ===== 主体 =====
.config-card {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
}

.config-container {
  padding: 16px 18px 4px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 60vh;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #bfe3f9;
    border-radius: 8px;
    border: 2px solid #f4fbff;

    &:hover {
      background: #9cd3f5;
    }
  }
}

// ===== 分区卡片 =====
.config-section {
  background: #ffffff;
  border-radius: 20px;
  padding: 14px 16px 16px;
  border: 3px solid $line;
  box-shadow: 0 4px 0 rgba(200, 224, 242, 0.5);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 0 rgba(200, 224, 242, 0.5);
  }

  &.section-blue   { border-color: #cfe9fb; .section-icon { background: #e3f3fe; } }
  &.section-green  { border-color: #cdefd9; .section-icon { background: #e4f8ec; } }
  &.section-purple { border-color: #e0dbfa; .section-icon { background: #efecfd; } }
  &.section-orange { border-color: #ffe4c2; .section-icon { background: #fff2e0; } }
  &.section-pink   { border-color: #ffd9e2; .section-icon { background: #ffeef2; } }
  &.section-gray   { border-color: #e5e9f0; .section-icon { background: #f0f2f6; } }

  &.disabled-section {
    opacity: 0.65;
    pointer-events: none;

    &:hover {
      transform: none;
    }
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;

  .section-icon {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    transition: transform 0.3s ease;
  }

  &:hover .section-icon {
    transform: rotate(-10deg) scale(1.1);
  }

  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: $ink;
    margin: 0;
    flex: 1;
    letter-spacing: 1px;
  }

  .badge {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 999px;
    font-weight: 700;
    letter-spacing: 1px;

    &.badge-required {
      background: #ffe9e9;
      color: #f26d6d;
      border: 2px solid #ffc9c9;
    }

    &.badge-optional {
      background: #e4f8ec;
      color: #3fae70;
      border: 2px solid #bdebd0;
    }

    &.badge-coming {
      background: #f0f2f6;
      color: #9aa7b5;
      border: 2px solid #dde3ec;
    }
  }
}

// ===== 解析模式卡片 =====
.mode-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #f7fbff;
  border: 3px solid #e3eef8;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

  &:hover {
    transform: translateY(-2px) scale(1.01);
    border-color: #a8d8f8;
    box-shadow: 0 5px 0 rgba(168, 216, 248, 0.35);
  }

  &:active {
    transform: translateY(1px) scale(0.99);
    box-shadow: none;
  }

  &.active {
    background: linear-gradient(135deg, #e9f6ff 0%, #ddf2ff 100%);
    border-color: $blue;
    box-shadow: 0 5px 0 rgba(88, 182, 240, 0.35);

    .mode-emoji {
      background: #ffffff;
      border-color: $blue;
      animation: wiggle 0.5s ease;
    }

    .mode-check {
      background: $blue;
      border-color: $blue;
      color: #ffffff;
      box-shadow: 0 3px 0 $blue-dark;
    }
  }

  .mode-emoji {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    background: #ffffff;
    border: 3px solid #e3eef8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
    transition: all 0.25s ease;
  }

  .mode-info {
    flex: 1;
    min-width: 0;

    .mode-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;

      span:first-child {
        font-size: 15px;
        font-weight: 700;
        color: $ink;
      }

      .tag {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        font-weight: 700;
        letter-spacing: 1px;

        &.tag-green {
          background: #dff6e8;
          color: #2e9e63;
          border: 1.5px solid #b3e8ca;
        }

        &.tag-orange {
          background: #fff1dd;
          color: #d07f1f;
          border: 1.5px solid #ffdcab;
        }
      }
    }

    .mode-desc {
      font-size: 12px;
      color: $sub-ink;
      line-height: 1.5;
      margin: 0;
    }
  }

  .mode-check {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 3px solid #dbe6f0;
    background: #ffffff;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

@keyframes wiggle {
  0%, 100% { transform: rotate(0); }
  25% { transform: rotate(-10deg); }
  60% { transform: rotate(8deg); }
}

// ===== 语言设置 =====
.lang-container {
  display: flex;
  align-items: center;
  gap: 14px;
}

.lang-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .lang-label {
    font-size: 13px;
    font-weight: 700;
    color: $ink;
    letter-spacing: 0.5px;
  }

  .lang-select {
    width: 100%;

    :deep(.el-input__wrapper) {
      border-radius: 14px;
      box-shadow: 0 0 0 2px #dcebf7 inset;
      transition: box-shadow 0.25s ease;

      &:hover {
        box-shadow: 0 0 0 2px #a8d8f8 inset;
      }

      &.is-focus {
        box-shadow: 0 0 0 2px $blue inset;
      }
    }
  }
}

.swap-fish {
  position: relative;
  width: 44px;
  height: 44px;
  margin-top: 22px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e9f6ff;
  border: 3px solid #cfe9fb;

  .fish {
    font-size: 20px;
    animation: fish-swim 2.4s ease-in-out infinite;
  }

  .fish-trail {
    position: absolute;
    left: -14px;
    font-size: 10px;
    color: #9cd3f5;
    animation: trail-fade 2.4s ease-in-out infinite;
  }
}

@keyframes fish-swim {
  0%, 100% { transform: translateX(-3px) rotate(0); }
  50% { transform: translateX(3px) rotate(6deg); }
}

@keyframes trail-fade {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 0.9; }
}

// ===== 选项卡片 =====
.option-card {
  background: #f9fcff;
  border: 3px solid #eaf2fa;
  border-radius: 16px;
  padding: 12px 14px;

  .option-main {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
  }

  .option-info {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    flex: 1;
  }

  .option-emoji {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    background: #ffffff;
    border: 2px solid #e3eef8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }

  .option-text {
    flex: 1;

    .option-label {
      font-size: 14px;
      font-weight: 700;
      color: $ink;
      margin-bottom: 3px;
      display: block;
    }

    .option-description {
      font-size: 12px;
      color: $sub-ink;
      margin: 0;
      line-height: 1.5;
    }
  }

  .option-warning {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    padding: 8px 12px;
    background: #fff7e0;
    border: 2px dashed #f5ce6b;
    border-radius: 12px;
    font-size: 12px;
    color: #9a7516;
    font-weight: 600;
  }
}

// el-switch 卡通配色
.cartoon-switch {
  :deep(.el-switch.is-checked .el-switch__core) {
    background-color: $purple;
    border-color: $purple;
  }
}

.concurrency-input {
  flex-shrink: 0;

  :deep(.el-input__wrapper) {
    border-radius: 12px;
    box-shadow: 0 0 0 2px #f0e3d2 inset;
  }
}

.full-width {
  width: 100%;

  :deep(.el-input__wrapper) {
    border-radius: 14px;
  }
}

// ===== 翻译模型（厂商/模型/Base URL）=====
.provider-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.provider-chip {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 8px 10px;
  background: #f7fbff;
  border: 3px solid #e3eef8;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
  user-select: none;

  .provider-name {
    font-size: 11px;
    font-weight: 700;
    color: $ink;
    text-align: center;
    line-height: 1.2;
    word-break: keep-all;
  }

  &:hover {
    transform: translateY(-2px);
    border-color: #a8d8f8;
    box-shadow: 0 4px 0 rgba(168, 216, 248, 0.35);
  }

  &:active {
    transform: translateY(1px);
    box-shadow: none;
  }

  &.active {
    background: linear-gradient(135deg, #e9f6ff 0%, #ddf2ff 100%);
    border-color: $blue;
    box-shadow: 0 4px 0 rgba(88, 182, 240, 0.35);

    .provider-name {
      color: $blue-dark;
    }

    // provider-emoji removed
  }
}

.provider-desc {
  margin: 10px 2px 0;
  font-size: 12px;
  color: $sub-ink;
  line-height: 1.5;
}

.model-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.model-field {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .model-label {
    font-size: 13px;
    font-weight: 700;
    color: $ink;
    letter-spacing: 0.5px;
  }

  .full-width {
    :deep(.el-input__wrapper) {
      box-shadow: 0 0 0 2px #e2e6ee inset;
      transition: box-shadow 0.25s ease;

      &:hover {
        box-shadow: 0 0 0 2px #b9c6d8 inset;
      }

      &.is-focus {
        box-shadow: 0 0 0 2px #9aa7c0 inset;
      }
    }
  }
}

.key-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  font-weight: 600;
  color: $blue-dark;
  text-decoration: none;
  transition: all 0.2s ease;

  &:hover {
    color: $blue;
    transform: translateX(2px);
  }
}

// ===== API Key =====
.api-key-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.api-key-input {
  flex: 1;

  :deep(.el-input__wrapper) {
    border-radius: 14px;
    box-shadow: 0 0 0 2px #f6dbe2 inset;
    transition: box-shadow 0.25s ease;

    &:hover {
      box-shadow: 0 0 0 2px #f3b9c7 inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 2px $pink inset;
    }
  }
}

.test-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  height: 40px;
  border: 3px solid $blue;
  background: #ffffff;
  color: $blue;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  box-shadow: 0 4px 0 rgba(88, 182, 240, 0.35);
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);

  &:hover:not(:disabled) {
    background: $blue;
    color: #ffffff;
    transform: translateY(-2px);
    box-shadow: 0 6px 0 rgba(88, 182, 240, 0.35);
  }

  &:active:not(:disabled) {
    transform: translateY(2px);
    box-shadow: 0 1px 0 rgba(88, 182, 240, 0.35);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
  }

  &.success {
    border-color: $green;
    color: #2e9e63;
    background: #eefbf3;
    box-shadow: 0 4px 0 rgba(111, 206, 147, 0.35);
  }

  &.error {
    border-color: #f58b8b;
    color: #f26d6d;
    background: #fff1f1;
    box-shadow: 0 4px 0 rgba(245, 139, 139, 0.3);
  }
}

.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2.5px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.test-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;

  &.success {
    background: #eefbf3;
    color: #2e9e63;
    border: 2px dashed #a5e3c1;
  }

  &.error {
    background: #fff1f1;
    color: #f26d6d;
    border: 2px dashed #f8bcbc;
  }
}

// ===== 底部按钮 =====
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 14px 18px 18px;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 24px;
  border-radius: 16px;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);

  &:active {
    transform: translateY(2px);
  }

  &.btn-cancel {
    background: #ffffff;
    color: $sub-ink;
    border: 3px solid #e2e8f0;
    box-shadow: 0 4px 0 #e2e8f0;

    &:hover {
      color: $ink;
      border-color: #c9d4e0;
      transform: translateY(-2px);
      box-shadow: 0 6px 0 #e2e8f0;
    }

    &:active {
      box-shadow: 0 1px 0 #e2e8f0;
    }
  }

  &.btn-translate {
    background: linear-gradient(135deg, #66c0f5 0%, #4aa9ec 100%);
    color: #ffffff;
    border: 3px solid #ffffff;
    box-shadow: 0 5px 0 $blue-dark;
    text-shadow: 0 1px 0 rgba(46, 139, 199, 0.4);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 7px 0 $blue-dark;
    }

    &:active:not(:disabled) {
      box-shadow: 0 1px 0 $blue-dark;
    }

    &:disabled {
      background: #dde4ec;
      color: #a6b2c0;
      box-shadow: 0 4px 0 #cbd4de;
      cursor: not-allowed;
      text-shadow: none;
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

<!-- 非 scoped：Element Plus 会把自定义 class 直接挂在 .el-dialog 元素上，需全局覆盖其默认白色底板 -->
<style lang="scss">
.translation-config-dialog.el-dialog {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  overflow: visible;
  border: none;
  // 保留 Element Plus 默认定位，避免弹窗贴顶
  margin: var(--el-dialog-margin-top, 15vh) auto 50px;
  outline: none;

  .el-dialog__header,
  .el-dialog__footer {
    padding: 0;
    margin: 0;
    background: transparent;
  }

  .el-dialog__body {
    padding: 0;
    background: transparent;
  }
}

.el-overlay:has(.translation-config-dialog) {
  background-color: rgba(46, 90, 122, 0.45);
  backdrop-filter: blur(3px);
}
</style>
