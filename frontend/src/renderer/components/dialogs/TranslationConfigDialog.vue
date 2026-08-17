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
    <!-- 自定义标题 -->
    <div class="dialog-header">
      <div class="header-content">
        <svg class="header-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M12.87 15.07L10.33 12.56L10.36 12.53C12.1 10.59 13.34 8.36 14.07 6H17V4H10V2H8V4H1V5.99H12.17C11.5 7.92 10.44 9.75 9 11.35C8.07 10.32 7.3 9.19 6.69 8H4.69C5.42 9.63 6.42 11.17 7.67 12.56L2.58 17.58L4 19L9 14L12.11 17.11L12.87 15.07ZM18.5 10H16.5L12 22H14L15.12 19H19.87L21 22H23L18.5 10ZM15.88 17L17.5 12.67L19.12 17H15.88Z" fill="currentColor"/>
        </svg>
        <h2 class="header-title">翻译配置</h2>
      </div>
      <button class="close-btn" @click="handleCancel">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
          <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <div class="config-card">
      <div class="config-container">
      <!-- 解析模式选择 -->
      <div class="config-section">
        <div class="section-header">
          <div class="section-icon-wrapper">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <h3 class="section-title">解析模式</h3>
          <span class="required-badge">必选</span>
        </div>
        <div class="config-content">
          <div class="mode-cards">
            <div 
              class="mode-card"
              :class="{ 'active': !config.useDps }"
              @click="config.useDps = false"
            >
              <div class="card-icon python-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path d="M9.585 11.692h4.328s2.432.039 2.432-2.35V5.391S16.714 3 11.936 3C7.362 3 7.647 3 7.647 3L7.638 5.32h4.368v.647H6.647S3 5.782 3 10.349v3.984s-.164 2.453 2.388 2.453h1.396V13.73s-.193-2.388 2.35-2.388h4.328z" stroke="currentColor" stroke-width="1.5"/>
                  <circle cx="8.5" cy="5.5" r=".9" fill="currentColor"/>
                </svg>
              </div>
              <div class="card-content">
                <div class="card-title">
                  <span>Python 解析</span>
                  <span class="badge badge-success">推荐</span>
                </div>
                <p class="card-desc">使用人工标注结果，翻译质量更高，适合精细化翻译</p>
              </div>
              <div class="card-check">
                <svg v-if="!config.useDps" width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M16.667 5L7.5 14.167 3.333 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>

            <div 
              class="mode-card"
              :class="{ 'active': config.useDps }"
              @click="config.useDps = true"
            >
              <div class="card-icon dps-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="card-content">
                <div class="card-title">
                  <span>DPS/OCR 解析</span>
                  <span class="badge badge-info">快速</span>
                </div>
                <p class="card-desc">直接使用OCR识别结果，无需人工标注，快速开始</p>
              </div>
              <div class="card-check">
                <svg v-if="config.useDps" width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M16.667 5L7.5 14.167 3.333 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 语言设置 -->
      <div class="config-section">
        <div class="section-header">
          <div class="section-icon-wrapper">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12.87 15.07L10.33 12.56L10.36 12.53C12.1 10.59 13.34 8.36 14.07 6H17V4H10V2H8V4H1V5.99H12.17C11.5 7.92 10.44 9.75 9 11.35C8.07 10.32 7.3 9.19 6.69 8H4.69C5.42 9.63 6.42 11.17 7.67 12.56L2.58 17.58L4 19L9 14L12.11 17.11L12.87 15.07ZM18.5 10H16.5L12 22H14L15.12 19H19.87L21 22H23L18.5 10ZM15.88 17L17.5 12.67L19.12 17H15.88Z" fill="currentColor"/>
            </svg>
          </div>
          <h3 class="section-title">语言设置</h3>
        </div>
        <div class="config-content">
          <div class="lang-container">
            <div class="lang-item">
              <label class="lang-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2"/>
                </svg>
                源语言
              </label>
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
            
            <div class="arrow-wrapper">
              <svg class="arrow-icon" width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14m0 0l-4-4m4 4l-4 4" stroke="url(#arrow-gradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <defs>
                  <linearGradient id="arrow-gradient" x1="5" y1="12" x2="19" y2="12">
                    <stop offset="0%" stop-color="#4facfe"/>
                    <stop offset="100%" stop-color="#00f2fe"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            
            <div class="lang-item">
              <label class="lang-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 10h6M12 7v10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                目标语言
              </label>
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
      </div>

      <!-- 高级选项 -->
      <div class="config-section">
        <div class="section-header">
          <div class="section-icon-wrapper">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.604.852.997 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3 class="section-title">高级选项</h3>
          <span class="optional-badge">可选</span>
        </div>
        <div class="config-content">
          <div class="option-card">
            <div class="option-main">
              <div class="option-info">
                <svg class="option-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <div class="option-text">
                  <label class="option-label">聚合标题</label>
                  <p class="option-description">将相邻的同类型标题合并为一个翻译任务</p>
                </div>
              </div>
              <el-switch v-model="config.aggregateTitles" size="large" />
            </div>
            <div v-if="config.aggregateTitles" class="option-warning">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>不推荐开启，可能影响翻译质量</span>
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="section-header">
          <div class="section-icon-wrapper">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 2v6m0 8v6M4.93 4.93l4.24 4.24m5.66 5.66 4.24 4.24M2 12h6m8 0h6M4.93 19.07l4.24-4.24m5.66-5.66 4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <h3 class="section-title">并发控制</h3>
          <span class="optional-badge">可选</span>
        </div>
        <div class="config-content">
          <div class="option-card">
            <div class="option-main">
              <div class="option-info">
                <svg class="option-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div class="option-text">
                  <label class="option-label">翻译并发数</label>
                  <p class="option-description">控制同时请求大模型的任务数量，建议 3-5，过高可能触发限流</p>
                </div>
              </div>
              <el-input-number v-model="config.maxConcurrent" :min="1" :max="20" :step="1" class="concurrency-input" />
            </div>
          </div>
        </div>
      </div>

      <!-- 翻译模型配置（待实现） -->
      <div class="config-section disabled-section">
        <div class="section-header">
          <div class="section-icon-wrapper disabled">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2"/>
              <path d="M12 22V12M22 10l-10 5M2 10l10 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3 class="section-title">翻译模型</h3>
          <span class="coming-soon-badge">即将推出</span>
        </div>
        <div class="config-content">
          <el-select v-model="config.translationModel" disabled placeholder="选择翻译模型" class="full-width">
            <el-option label="OpenAI GPT-4" value="gpt-4" />
            <el-option label="OpenAI GPT-3.5" value="gpt-3.5-turbo" />
            <el-option label="Claude 3" value="claude-3" />
          </el-select>
        </div>
      </div>

      <!-- API密钥配置 -->
      <div class="config-section">
        <div class="section-header">
          <div class="section-icon-wrapper">
            <svg class="section-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3 class="section-title">API密钥</h3>
          <span class="required-badge">必填</span>
        </div>
        <div class="config-content">
          <div class="api-key-wrapper">
            <el-input 
              v-model="config.apiKey" 
              type="password" 
              placeholder="输入DeepSeek API密钥" 
              show-password 
              class="api-key-input"
              @input="handleApiKeyChange"
            />
            <button 
              class="test-btn" 
              @click="handleTestApiKey"
              :disabled="!config.apiKey || testing"
              :class="{ 'success': testSuccess, 'error': testError }"
            >
              <svg v-if="!testing && !testSuccess && !testError" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M9 11l3 3L22 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="loading-spinner-small" v-if="testing"></span>
              <svg v-if="testSuccess" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-if="testError" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ testing ? '测试中...' : (testSuccess ? '测试成功' : (testError ? '测试失败' : '测试连接')) }}
            </button>
          </div>
          <p v-if="testSuccess" class="test-message success">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            API Key 有效，已保存到本地
          </p>
          <p v-if="testError" class="test-message error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            {{ testErrorMessage }}
          </p>
        </div>
      </div>
    </div>

      <div class="dialog-footer">
        <button class="footer-btn btn-cancel" @click="handleCancel">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          取消
        </button>
        <button 
          class="footer-btn btn-translate" 
          @click="handleStartTranslate"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14m-7-7l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          开始翻译
        </button>
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
  translationModel: 'gpt-4',
  apiKey: '',
  maxConcurrent: 5
})

const testing = ref(false)
const testSuccess = ref(false)
const testError = ref(false)
const testErrorMessage = ref('')

// 监听对话框打开状态，每次打开时加载 API Key
watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    // 对话框打开时加载已保存的 API Key
    await loadSavedApiKey()
  }
})

// 初始化：加载保存的 API Key（首次挂载）
onMounted(async () => {
  if (props.modelValue) {
    await loadSavedApiKey()
  }
})

// 加载已保存的 API Key
const loadSavedApiKey = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/translation/config/api-key')
    if (response.data.code === 200 && response.data.data.api_key) {
      config.value.apiKey = response.data.data.api_key
      console.log('加载已保存的 API Key:', response.data.data.masked_key)
    }
  } catch (error) {
    console.log('未找到已保存的 API Key')
  }
}

// API Key 变化时重置测试状态
const handleApiKeyChange = () => {
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''
}

// 测试 API Key
const handleTestApiKey = async () => {
  if (!config.value.apiKey || !config.value.apiKey.trim()) {
    window.$toast?.warning('请先输入 API Key')
    return
  }

  testing.value = true
  testSuccess.value = false
  testError.value = false
  testErrorMessage.value = ''

  try {
    // 测试连接
    const response = await axios.post(
      'http://localhost:8000/api/v1/translation/test',
      null,
      {
        params: {
          api_key: config.value.apiKey
        }
      }
    )

    if (response.data.code === 200 && response.data.data.success) {
      testSuccess.value = true
      window.$toast?.success('API Key 验证成功')
      
      // 测试成功后保存 API Key
      await saveApiKey()
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

// 保存 API Key
const saveApiKey = async () => {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/translation/config/api-key',
      null,
      {
        params: {
          api_key: config.value.apiKey
        }
      }
    )

    if (response.data.code === 200) {
      console.log('API Key 已保存:', response.data.data.masked_key)
    }
  } catch (error) {
    console.error('保存 API Key 失败:', error)
  }
}

// 取消
const handleCancel = () => {
  dialogVisible.value = false
}

const handleStartTranslate = async () => {
  if (!config.value.apiKey || !config.value.apiKey.trim()) {
    window.$toast?.warning('请先输入DeepSeek API密钥')
    return
  }

  if (!props.pdfName) {
    window.$toast?.error('缺少PDF名称')
    return
  }

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
      maxConcurrent: config.value.maxConcurrent
    }
  })
}

// 重置配置
watch(dialogVisible, (newVal, oldVal) => {
  if (newVal) {
    // 打开时重置配置
    config.value = {
      useDps: false,
      sourceLang: 'en',
      targetLang: 'zh-CN',
      aggregateTitles: false,
      translationModel: 'gpt-4',
      apiKey: '',
      maxConcurrent: 5
    }
  } else if (oldVal === true && newVal === false) {
    // 关闭时触发关闭事件
    emit('dialog-closed')
  }
})

onUnmounted(() => {
  // 清理逻辑（如需）
})
</script>

<style scoped lang="scss">
.translation-config-dialog {
  :deep(.el-dialog) {
    background: transparent;
    border-radius: 0;
    box-shadow: none;
    padding: 0;
    overflow: visible;
    border: none;
    margin: 0;
    outline: none;
  }

  :deep(.el-overlay) {
    background-color: rgba(0, 0, 0, 0.5);
  }

  :deep(.el-dialog__body) {
    padding: 0;
    background: transparent;
    backdrop-filter: blur(10px);
  }

  :deep(.el-dialog__footer) {
    padding: 0;
    background: transparent;
  }
}

// 自定义标题
.dialog-header {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  margin: 12px 12px 0 12px;
  box-shadow: 0 4px 20px rgba(79, 172, 254, 0.3);

  .header-content {
    display: flex;
    align-items: center;
    gap: 10px;
    position: relative;
    z-index: 1;
  }

  .header-icon {
    width: 20px;
    height: 20px;
    color: white;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    padding: 3px;
    backdrop-filter: blur(10px);
  }

  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: white;
    margin: 0;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  }

  .close-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    z-index: 1;

    svg {
      stroke: white;
    }

    &:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: scale(1.05);
    }

    &:active {
      transform: scale(0.95);
    }
  }
}

.config-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 12px;
  margin: 0 12px 12px 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.config-container {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 65vh;
  overflow-y: auto;

  // 美化滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    border-radius: 3px;

    &:hover {
      background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
    }
  }
}

.config-section {
  background: white;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);

  &:hover {
    box-shadow: 0 4px 20px rgba(79, 172, 254, 0.15);
    transform: translateY(-2px);
  }

  &.disabled-section {
    opacity: 0.6;
    background: #fafafa;
    pointer-events: none;

    &:hover {
      transform: none;
    }
  }
}

.translate-progress {
  padding: 0 32px 24px;
  
  :deep(.el-progress__text) {
    font-size: 12px !important;
    font-weight: 600;
  }

  :deep(.el-progress-bar__outer) {
    border-radius: 5px;
    overflow: hidden;
  }

  :deep(.el-progress-bar__inner) {
    border-radius: 5px;
    transition: width 0.3s ease, background-color 0.3s ease;
  }
}

.translate-progress-text {
  margin-top: 10px;
  font-size: 13px;
  color: #495057;
  font-weight: 500;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;

  .section-icon-wrapper {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.disabled {
      background: #ddd;
    }

    .section-icon {
      stroke: white;
      fill: white;
    }
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
    flex: 1;
  }

  .required-badge {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
    color: white;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
  }

  .optional-badge {
    background: linear-gradient(135deg, #74ebd5 0%, #9face6 100%);
    color: white;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .coming-soon-badge {
    background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
    color: white;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }
}

.config-content {
  padding-left: 48px;
}

// 模式卡片
.mode-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    transform: scaleY(0);
    transition: transform 0.3s ease;
  }

  &:hover {
    background: #f0f8ff;
    border-color: #4facfe;
    transform: translateX(4px);
  }

  &.active {
    background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%);
    border-color: #4facfe;
    box-shadow: 0 4px 16px rgba(79, 172, 254, 0.25);

    &::before {
      transform: scaleY(1);
    }

    .card-icon {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      color: white;
    }
  }

  .card-icon {
    width: 52px;
    height: 52px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.3s ease;
    background: white;
    border: 2px solid #e9ecef;

    &.python-icon {
      color: #4facfe;
    }

    &.dps-icon {
      color: #00c9ff;
    }
  }

  .card-content {
    flex: 1;

    .card-title {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 6px;

      span:first-child {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }

      .badge {
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;

        &.badge-success {
          background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
          color: #0d6832;
        }

        &.badge-info {
          background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%);
          color: #8b4513;
        }
      }
    }

    .card-desc {
      font-size: 13px;
      color: #6c757d;
      line-height: 1.5;
      margin: 0;
    }
  }

  .card-check {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.3s ease;

    svg {
      stroke: white;
    }
  }

  &.active .card-check {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    border-color: #4facfe;
    box-shadow: 0 2px 8px rgba(79, 172, 254, 0.4);
  }
}

// 语言设置
.lang-container {
  display: flex;
  align-items: center;
  gap: 20px;
}

.lang-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;

  .lang-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #495057;

    svg {
      stroke: #4facfe;
    }
  }

  .lang-select {
    width: 100%;

    :deep(.el-input__wrapper) {
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.2);
      }
    }
  }
}

.arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 28px;
  flex-shrink: 0;

  .arrow-icon {
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0.6;
      transform: translateX(0);
    }
    50% {
      opacity: 1;
      transform: translateX(4px);
    }
  }
}

// 高级选项
.option-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 18px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;

  &:hover {
    background: #f0f8ff;
    border-color: #4facfe;
  }

  .option-main {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .option-info {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;
  }

  .option-icon {
    width: 24px;
    height: 24px;
    stroke: #4facfe;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .option-text {
    flex: 1;

    .option-label {
      font-size: 15px;
      font-weight: 600;
      color: #2c3e50;
      margin-bottom: 6px;
      display: block;
    }

    .option-description {
      font-size: 13px;
      color: #6c757d;
      margin: 0;
      line-height: 1.5;
    }
  }

  .option-warning {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    padding: 10px 12px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    font-size: 12px;
    color: #856404;

    svg {
      stroke: #856404;
      flex-shrink: 0;
    }
  }
}

.full-width {
  width: 100%;

  :deep(.el-input__wrapper) {
    border-radius: 10px;
  }
}

// API Key 样式
.api-key-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.api-key-input {
  flex: 1;

  :deep(.el-input__wrapper) {
    border-radius: 10px;
  }
}

.test-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  height: 40px;
  border: 2px solid #4facfe;
  background: white;
  color: #4facfe;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  flex-shrink: 0;

  svg {
    stroke: currentColor;
    flex-shrink: 0;
  }

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.success {
    border-color: #67c23a;
    color: #67c23a;
    background: #f0f9ff;

    &:hover {
      background: #67c23a;
      color: white;
    }
  }

  &.error {
    border-color: #f56c6c;
    color: #f56c6c;
    background: #fef0f0;

    &:hover {
      background: #f56c6c;
      color: white;
    }
  }
}

.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.test-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;

  svg {
    stroke: currentColor;
    flex-shrink: 0;
  }

  &.success {
    background: #f0f9ff;
    color: #67c23a;
    border: 1px solid #b3e19d;
  }

  &.error {
    background: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fbc4c4;
  }
}

.concurrency-input {
  :deep(.el-input__wrapper) {
    border-radius: 10px;
  }
}

// 底部按钮
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px 16px;
  background: white;
  border-top: 1px solid #f0f0f0;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  svg {
    width: 16px;
    height: 16px;
  }

  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
  }

  &:hover::before {
    width: 300px;
    height: 300px;
  }

  &:active {
    transform: scale(0.96);
  }

  &.btn-cancel {
    background: #f8f9fa;
    color: #6c757d;
    border: 1px solid #dee2e6;

    svg {
      stroke: #6c757d;
    }

    &:hover {
      background: #e9ecef;
      border-color: #adb5bd;
    }
  }

  &.btn-translate {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    color: #495057;
    box-shadow: 0 4px 16px rgba(168, 237, 234, 0.4);
    opacity: 0.6;
    cursor: not-allowed;

    svg {
      stroke: #495057;
    }

    .coming-tag {
      font-size: 10px;
      padding: 2px 6px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 8px;
      margin-left: 4px;
    }
  }
}

// 加载动画
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
