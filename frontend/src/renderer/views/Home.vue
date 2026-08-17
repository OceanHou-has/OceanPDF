<template>
  <div class="home-page">
    <!-- 侧边导航栏 -->
    <aside class="sidebar">
      <div class="logo-section">
        <img class="logo-icon" :src="waveIcon" alt="OceanPDF" />
        <h1 class="app-title">OceanPDF</h1>
      </div>
      
      <nav class="nav-menu">
        <div 
          class="nav-item" 
          :class="{ active: currentView === 'upload' }"
          @click="switchView('upload')"
        >
          <el-icon><Upload /></el-icon>
          <span>上传翻译</span>
        </div>
        <div 
          class="nav-item"
          :class="{ active: currentView === 'parsed' }"
          @click="switchView('parsed')"
        >
          <el-icon><FolderOpened /></el-icon>
          <span>已解析PDF</span>
        </div>
        <div 
          class="nav-item"
          :class="{ active: currentView === 'setting' }"
          @click="switchView('setting')"
        >
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </div>
      </nav>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-container">
      <div class="main-surface">
        <!-- 顶部栏 -->
        <header class="top-bar">
          <div class="page-info">
            <h2 class="page-title">{{ pageTitle }}</h2>
            <p class="page-desc">{{ pageDesc }}</p>
          </div>
          <div class="top-actions">
            <div v-if="currentView === 'upload'" class="parallelism-setting">
              <span class="parallelism-label">并行度</span>
              <el-input-number v-model="parallelism" :min="1" :max="5" :step="1" />
            </div>
            <!-- 刷新按钮（仅在已解析PDF视图显示） -->
            <Button1
              v-if="currentView === 'parsed'"
              class="refresh-button"
              size="small"
              :class="{ 'is-loading': isRefreshing }"
              @click="handleRefresh"
              aria-label="刷新列表"
              title="刷新列表"
            >
              <el-icon :class="{ 'rotating': isRefreshing }"><Refresh /></el-icon>
              <span>刷新列表</span>
            </Button1>
            <!-- 一键下载按钮（仅在已解析PDF视图显示） -->
            <Button1
              v-if="currentView === 'parsed'"
              class="download-button"
              size="small"
              @click="handleBatchDownload"
              aria-label="一键下载"
              title="一键下载"
            >
              <el-icon><Download /></el-icon>
              <span>一键下载</span>
            </Button1>
            <!-- 一键翻译按钮（仅在已解析PDF视图显示） -->
            <Button1
              v-if="currentView === 'parsed'"
              class="translate-button"
              size="small"
              @click="handleBatchTranslate"
              aria-label="一键翻译"
              title="一键翻译"
            >
              <el-icon><DocumentCopy /></el-icon>
              <span>一键翻译</span>
            </Button1>
            <Button1 class="help-button" size="small" @click="handleHelp" aria-label="帮助" title="帮助">
              <el-icon><QuestionFilled /></el-icon>
              <span>帮助</span>
            </Button1>
          </div>
        </header>

        <!-- 内容区域 -->
        <div class="content-section">
          <!-- 上传面板 -->
          <div v-show="currentView === 'upload'" class="view-container upload-view">
            <UploadPanel :parallelism="parallelism" @go-parsed="switchView('parsed')" />
          </div>
          
          <!-- 已解析PDF列表 -->
          <div v-show="currentView === 'parsed'" class="view-container list-view">
            <ParsedList
              ref="parsedListRef"
              :selection-mode="selectionMode"
              @cancel="handleCancelSelection"
              @confirm-translate="handleConfirmTranslate"
            />
          </div>
          
          <!-- 设置页面 -->
          <div v-show="currentView === 'setting'" class="view-container setting-view">
            <Settings />
          </div>
        </div>
      </div>
    </main>

    <!-- 批量翻译配置对话框 -->
    <el-dialog
      v-model="batchTranslateDialogVisible"
      title="批量翻译配置"
      width="560px"
      :close-on-click-modal="false"
      class="batch-translate-dialog"
    >
      <div class="batch-translate-form">
        <div class="form-item">
          <label class="form-label">解析模式</label>
          <div class="mode-selector">
            <div
              class="mode-option"
              :class="{ active: !batchTranslateConfig.useDps }"
              @click="batchTranslateConfig.useDps = false"
            >
              <span>Python 解析</span>
              <span class="mode-badge recommend">推荐</span>
            </div>
            <div
              class="mode-option"
              :class="{ active: batchTranslateConfig.useDps }"
              @click="batchTranslateConfig.useDps = true"
            >
              <span>DPS/OCR 解析</span>
              <span class="mode-badge fast">快速</span>
            </div>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">语言设置</label>
          <div class="lang-row">
            <el-select v-model="batchTranslateConfig.sourceLang" placeholder="源语言" class="lang-select">
              <el-option label="🇬🇧 英语" value="en" />
              <el-option label="🇨🇳 中文" value="zh" />
              <el-option label="🇯🇵 日语" value="ja" />
              <el-option label="🇰🇷 韩语" value="ko" />
              <el-option label="🇫🇷 法语" value="fr" />
              <el-option label="🇩🇪 德语" value="de" />
              <el-option label="🇪🇸 西班牙语" value="es" />
            </el-select>
            <el-icon class="lang-arrow"><ArrowRight /></el-icon>
            <el-select v-model="batchTranslateConfig.targetLang" placeholder="目标语言" class="lang-select">
              <el-option label="🇨🇳 中文简体" value="zh-CN" />
              <el-option label="🇭🇰 中文繁体" value="zh-TW" />
              <el-option label="🇬🇧 英语" value="en" />
              <el-option label="🇯🇵 日语" value="ja" />
              <el-option label="🇰🇷 韩语" value="ko" />
            </el-select>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">并发数</label>
          <el-input-number v-model="batchTranslateConfig.maxConcurrent" :min="1" :max="20" :step="1" />
          <span class="form-hint">控制同时请求大模型的任务数量</span>
        </div>

        <div class="form-item">
          <label class="form-label">API 密钥 <span class="required">*</span></label>
          <el-input
            v-model="batchTranslateConfig.apiKey"
            type="password"
            placeholder="输入 DeepSeek API 密钥"
            show-password
          />
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="batchTranslateDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="isBatchTranslating" @click="confirmBatchTranslate">
            开始翻译 ({{ selectedPdfCount }} 个文件)
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { 
  Upload, 
  Setting, 
  QuestionFilled,
  FolderOpened,
  Refresh,
  DocumentCopy,
  ArrowRight,
  Download
} from '@element-plus/icons-vue'
import axios from 'axios'
import UploadPanel from '../components/UploadPanel.vue'
import ParsedList from './ParsedList.vue'
import Settings from './Settings.vue'
import Button1 from '../elements/button/button1.vue'
import waveIcon from '../elements/icon/海浪.svg'
import { generatePretranslation, startTranslation, getApiKey, getMaxConcurrent } from '../api/pdf'

// 当前视图
const currentView = ref('upload')
const parallelism = ref(2)
// ParsedList组件引用
const parsedListRef = ref(null)
// 刷新状态
const isRefreshing = ref(false)

// 选择模式：null | 'translate' | 'download'
const selectionMode = ref(null)

// 批量翻译相关
const batchTranslateDialogVisible = ref(false)
const isBatchTranslating = ref(false)
const batchTranslateConfig = ref({
  useDps: false,
  sourceLang: 'en',
  targetLang: 'zh-CN',
  maxConcurrent: 5,
  apiKey: ''
})

const selectedPdfCount = computed(() => {
  return parsedListRef.value?.selectedPdfs?.length || 0
})

// 页面标题和描述
const pageTitle = computed(() => {
  const titles = {
    upload: 'PDF文档翻译',
    parsed: '已解析PDF',
    setting: '系统设置'
  }
  return titles[currentView.value] || ''
})

const pageDesc = computed(() => {
  const descs = {
    upload: '上传PDF文档，智能解析并翻译为双语对照版本',
    parsed: '查看已经解析完成的PDF文档列表',
    setting: '配置翻译参数和API密钥'
  }
  return descs[currentView.value] || ''
})

// 切换视图
const switchView = async (view) => {
  currentView.value = view
  if (view === 'parsed') {
    await nextTick()
    handleRefresh()
  }
}

// 刷新PDF列表
const handleRefresh = async () => {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    if (parsedListRef.value && parsedListRef.value.loadList) {
      await parsedListRef.value.loadList()
    }
  } finally {
    isRefreshing.value = false
  }
}

const handleHelp = () => {
  window.$toast?.info('帮助文档开发中...')
}

// 进入批量下载选择模式
const handleBatchDownload = () => {
  selectionMode.value = 'download'
  window.$toast?.info('请选择要下载的文件，然后点击确认')
}

// 取消选择模式
const handleCancelSelection = () => {
  selectionMode.value = null
}

// 加载翻译配置默认值
const loadTranslationConfig = async () => {
  try {
    const [apiRes, concurrentRes] = await Promise.all([
      getApiKey().catch(() => null),
      getMaxConcurrent().catch(() => null)
    ])
    if (apiRes && apiRes.code === 200 && apiRes.data) {
      batchTranslateConfig.value.apiKey = apiRes.data.api_key || ''
    }
    if (concurrentRes && concurrentRes.code === 200 && concurrentRes.data) {
      batchTranslateConfig.value.maxConcurrent = concurrentRes.data.max_concurrent || 5
    }
  } catch (error) {
    console.log('加载翻译配置失败:', error)
  }
}

// 打开批量翻译对话框（由全选栏确认触发）
const handleConfirmTranslate = async () => {
  const selected = parsedListRef.value?.selectedPdfs || []
  if (selected.length === 0) {
    window.$toast?.warning('请先选择要翻译的文件')
    return
  }

  await loadTranslationConfig()
  batchTranslateDialogVisible.value = true
}

// 点击顶部栏一键翻译按钮：进入选择模式
const handleBatchTranslate = () => {
  selectionMode.value = 'translate'
  window.$toast?.info('请选择要翻译的文件，然后点击确认')
}

// 确认批量翻译
const confirmBatchTranslate = async () => {
  if (!batchTranslateConfig.value.apiKey || !batchTranslateConfig.value.apiKey.trim()) {
    window.$toast?.warning('请输入 DeepSeek API 密钥')
    return
  }

  const selected = [...(parsedListRef.value?.selectedPdfs || [])]
  if (selected.length === 0) {
    window.$toast?.warning('请先选择要翻译的文件')
    return
  }

  isBatchTranslating.value = true

  try {
    // 保存 API Key
    try {
      await axios.post(
        'http://localhost:8000/api/v1/translation/config/api-key',
        null,
        { params: { api_key: batchTranslateConfig.value.apiKey } }
      )
    } catch (e) {
      console.error('保存 API Key 失败:', e)
    }

    // 逐个启动翻译
    let successCount = 0
    let failCount = 0

    for (const pdfName of selected) {
      try {
        // 生成预翻译
        await generatePretranslation(pdfName, {
          source_lang: batchTranslateConfig.value.sourceLang,
          target_lang: batchTranslateConfig.value.targetLang,
          aggregate_titles: false,
          use_dps: batchTranslateConfig.value.useDps,
          force: false
        })

        // 启动翻译
        await startTranslation({
          pdf_name: pdfName,
          api_key: batchTranslateConfig.value.apiKey,
          use_dps: batchTranslateConfig.value.useDps,
          max_concurrent: batchTranslateConfig.value.maxConcurrent,
          enable_distribution: true
        })

        successCount++
      } catch (error) {
        console.error(`启动翻译失败 [${pdfName}]:`, error)
        failCount++
      }
    }

    batchTranslateDialogVisible.value = false

    if (failCount === 0) {
      window.$toast?.success(`成功启动 ${successCount} 个翻译任务`)
    } else {
      window.$toast?.warning(`成功 ${successCount} 个，失败 ${failCount} 个`)
    }

    // 刷新列表以显示翻译状态
    handleRefresh()
    // 退出选择模式
    handleCancelSelection()
  } catch (error) {
    window.$toast?.error('批量翻译失败：' + (error.message || '未知错误'))
  } finally {
    isBatchTranslating.value = false
  }
}
</script>

<style scoped lang="scss">
.home-page {
  display: flex;
  height: 100vh;
  padding: 20px 24px;
  gap: 20px;
  box-sizing: border-box;
  background:
    radial-gradient(1200px circle at 18% 8%, rgba(79, 107, 255, 0.12), transparent 55%),
    #F6F7FB;
  overflow: hidden;
}

// 侧边栏样式
.sidebar {
  width: 240px;
  height: 100%;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 18px;
  color: #111827;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 20px 50px rgba(17, 24, 39, 0.08),
    0 2px 8px rgba(17, 24, 39, 0.06);
  overflow: hidden;
  backdrop-filter: blur(10px);

  .logo-section {
    padding: 22px 20px;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    gap: 10px;

    .logo-icon {
      display: block;
      width: 28px;
      height: 28px;
      flex: 0 0 auto;
      filter: drop-shadow(0 6px 14px rgba(79, 107, 255, 0.22));
    }

    .app-title {
      font-size: 24px;
      font-weight: 700;
      margin: 0;
      letter-spacing: 0.6px;
      line-height: 1;
      color: #111827;
    }
  }

  .nav-menu {
    flex: 1;
    padding: 14px 0;

    .nav-item {
      position: relative;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      margin: 6px 10px;
      border-radius: 12px;
      cursor: pointer;
      transition: box-shadow 0.2s ease, transform 0.2s ease;
      font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      font-size: 16px;
      font-weight: 500;
      letter-spacing: 0.2px;
      line-height: 1.1;
      color: #111827;
      overflow: hidden;
      z-index: 1;

      // 滑动填充效果的背景层
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 0;
        height: 100%;
        background: linear-gradient(90deg, rgba(79, 107, 255, 0.08) 0%, rgba(79, 107, 255, 0.15) 100%);
        transition: width 0.3s ease-out;
        z-index: -1;
        border-radius: 12px;
      }

      .el-icon {
        font-size: 20px;
        color: rgba(17, 24, 39, 0.70);
      }

      &:hover::before {
        width: 100%;
      }

      &.active {
        background: rgba(79, 107, 255, 0.12);
        box-shadow: 0 6px 16px rgba(79, 107, 255, 0.16);
        color: #4F6BFF;

        .el-icon {
          color: #4F6BFF;
        }
      }
    }
  }
}

// 主内容区域
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.main-surface {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 18px;
  box-shadow:
    0 20px 50px rgba(17, 24, 39, 0.08),
    0 2px 8px rgba(17, 24, 39, 0.06);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

// 顶部栏
.top-bar {
  background: transparent;
  padding: 20px 24px;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .page-info {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #111827;
      margin: 0 0 8px 0;
    }

    .page-desc {
      font-size: 14px;
      color: #6B7280;
      margin: 0;
    }
  }

  .top-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-top: 4px;

    .parallelism-setting {
      display: flex;
      align-items: center;
      gap: 8px;

      .parallelism-label {
        font-size: 14px;
        color: #6B7280;
        user-select: none;
      }
    }

    .el-button {
      font-size: 14px;
      color: rgba(17, 24, 39, 0.72);

      .el-icon {
        margin-right: 4px;
      }
    }

    // 帮助按钮样式
    .help-button {
      --color-background: #FF8A4B;
      --color-background-hover: #FF6B2C;
      --color-outline: #FF8A4B40;
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
    }

    // 一键下载按钮样式
    .download-button {
      --color-background: #10B981;
      --color-background-hover: #059669;
      --color-outline: #10B98140;
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
    }

    // 一键翻译按钮样式
    .translate-button {
      --color-background: #9C27B0;
      --color-background-hover: #7B1FA2;
      --color-outline: #9C27B040;
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
    }

    // 刷新按钮样式
    .refresh-button {
      --color-background: #64B5F6;
      --color-background-hover: #42A5F5;
      --color-outline: #64B5F640;
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
        animation: rotate-once 0.6s ease-in-out;
      }

      :deep(.el-icon.rotating) {
        animation: rotate-continuous 1s linear infinite;
      }

      &:active :deep(.button_top) {
        transform: scale(0.95);
      }

      &:active :deep(.button_top span),
      &:active :deep(.button_top .el-icon) {
        text-shadow: none;
        filter: none;
      }

      &.is-loading {
        opacity: 0.8;
        cursor: wait;
      }

      @keyframes rotate-once {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes rotate-continuous {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
    }

    // 波纹和颜色动画
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
  }
}

// 上传区域 - 动态填充剩余空间
.content-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  min-height: 0;

  .view-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    
    &.upload-view {
      padding: 20px 24px 24px;
    }
    
    &.list-view {
      padding: 0;
    }
    
    &.setting-view {
      padding: 0;
    }
  }

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

// 响应式设计
@media (max-width: 768px) {
  .home-page {
    padding: 14px;
    gap: 14px;
  }

  .sidebar {
    width: 200px;
    border-radius: 16px;
  }

  .main-surface {
    border-radius: 16px;
  }

  .top-bar {
    padding: 16px 18px;

    .page-info {
      .page-title {
        font-size: 20px;
      }
    }
  }

  .content-section {
    .view-container {
      &.upload-view {
        padding: 16px 18px 18px;
      }
      
      &.list-view {
        padding: 0;
      }
    }
  }
}

// 批量翻译对话框样式
.batch-translate-dialog {
  :deep(.el-dialog__header) {
    font-weight: 600;
    font-size: 16px;
  }

  .batch-translate-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 8px 4px;

    .form-item {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .form-label {
        font-size: 14px;
        font-weight: 500;
        color: #374151;

        .required {
          color: #ef4444;
        }
      }

      .form-hint {
        font-size: 12px;
        color: #9ca3af;
      }
    }

    .mode-selector {
      display: flex;
      gap: 12px;

      .mode-option {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s;
        font-size: 14px;
        color: #4b5563;

        &:hover {
          border-color: #a78bfa;
          background: #faf5ff;
        }

        &.active {
          border-color: #9C27B0;
          background: #f3e8ff;
          color: #7B1FA2;
          font-weight: 500;
        }

        .mode-badge {
          font-size: 11px;
          padding: 2px 8px;
          border-radius: 10px;
          font-weight: 500;

          &.recommend {
            background: #d1fae5;
            color: #065f46;
          }

          &.fast {
            background: #dbeafe;
            color: #1e40af;
          }
        }
      }
    }

    .lang-row {
      display: flex;
      align-items: center;
      gap: 12px;

      .lang-select {
        flex: 1;
      }

      .lang-arrow {
        color: #9ca3af;
        font-size: 18px;
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
