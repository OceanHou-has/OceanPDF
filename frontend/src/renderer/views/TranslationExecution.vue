<template>
  <div class="translation-execution">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="navbar-left">
        <Button1 class="nav-btn back-btn" size="icon" @click="handleBack" aria-label="返回" title="返回">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Button1>
        <div class="navbar-title">
          <h2>{{ pdfName }}</h2>
          <span class="subtitle">AI论文翻译</span>
        </div>
      </div>
      <div class="navbar-right">
        <div class="translate-status" :class="statusClass">
          <div class="status-dot"></div>
          <span>{{ statusText }}</span>
        </div>
        <Button1 class="nav-btn refresh-btn" size="icon" @click="handleRefresh" aria-label="刷新翻译结果" title="刷新翻译结果">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" :class="{ spinning: isRefreshing }">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Button1>
        <Button1 class="nav-btn" size="icon" @click="handlePause" v-if="!isPaused && isTranslating" aria-label="暂停" title="暂停">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M10 4H6v16h4V4zM18 4h-4v16h4V4z" fill="currentColor"/>
          </svg>
        </Button1>
        <Button1 class="nav-btn" size="icon" @click="handleResume" v-if="isPaused" aria-label="继续" title="继续">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M8 5v14l11-7z" fill="currentColor"/>
          </svg>
        </Button1>
        <Button1 class="nav-btn" size="icon" @click="handleStop" v-if="isTranslating" aria-label="停止" title="停止">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="6" y="6" width="12" height="12" fill="currentColor"/>
          </svg>
        </Button1>
        <Button1 class="nav-btn export-btn" size="icon" :disabled="!isCompleted" @click="handleExport" aria-label="导出结果" title="导出结果">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Button1>
      </div>
    </div>

    <!-- 进度信息栏 -->
    <div class="progress-bar" v-if="isTranslating || isPaused || isCompleted">
      <div class="progress-info">
        <span class="progress-text">{{ progressMessage }}</span>
        <span class="progress-count">{{ currentCount }} / {{ totalCount }}</span>
      </div>
      <div class="progress-line">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="progress-stats">
        <span>进度: {{ progressPercent }}%</span>
        <span v-if="estimatedTime">预计剩余: {{ estimatedTime }}</span>
        <div class="translation-stats">
          <span class="stat-item success">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2"/>
            </svg>
            成功: {{ translationSuccess }}
          </span>
          <span class="stat-item failed" v-if="translationFailed > 0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2"/>
            </svg>
            失败: {{ translationFailed }}
          </span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <div class="viewer-toolbar">
        <div class="page-controls">
          <button class="mini-btn" @click="goPrevPage" :disabled="currentPage <= 0" title="上一页">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <div class="page-indicator">
            <span>第 {{ currentPage + 1 }} / {{ totalPages || 0 }} 页</span>
          </div>
          <button class="mini-btn" @click="goNextPage" :disabled="!totalPages || currentPage >= totalPages - 1" title="下一页">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="zoom-controls">
          <button class="mini-btn" @click="zoomOut" title="缩小">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="zoom-indicator">{{ Math.round(viewScale * 100) }}%</div>
          <button class="mini-btn" @click="zoomIn" title="放大">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="viewer-panels">
        <div class="content-panel pdf-panel original-panel">
          <div class="panel-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
              <path d="M14 2v6h6" stroke="currentColor" stroke-width="2"/>
            </svg>
            <h3>原文</h3>
          </div>
          <div class="panel-content pdf-viewer">
            <div v-if="!pageImage" class="empty-placeholder">
              <p>正在加载页面...</p>
            </div>
            <div v-else class="pdf-viewport" :class="{ 'is-panning': isPanning }" ref="originalViewport" @wheel="handleWheel" @mousedown="handleMouseDown">
              <div class="page-container">
                <div class="page-transform">
                  <div class="page-layer" :style="{ width: scaledDisplayWidth + 'px', height: scaledDisplayHeight + 'px' }">
                    <img class="pdf-image" :src="pageImage" :width="scaledDisplayWidth" :height="scaledDisplayHeight" draggable="false" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="content-panel pdf-panel translation-panel" :style="{ '--overlay-zoom-scale': viewScale }">
          <div class="panel-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12.87 15.07L10.33 12.56L10.36 12.53C12.1 10.59 13.34 8.36 14.07 6H17V4H10V2H8V4H1V5.99H12.17C11.5 7.92 10.44 9.75 9 11.35C8.07 10.32 7.3 9.19 6.69 8H4.69C5.42 9.63 6.42 11.17 7.67 12.56L2.58 17.58L4 19L9 14L12.11 17.11L12.87 15.07Z" fill="currentColor"/>
            </svg>
            <h3>译文</h3>
          </div>
          <div class="panel-content pdf-viewer">
            <div v-if="!pageImage" class="empty-placeholder">
              <p>正在加载页面...</p>
            </div>
            <div v-else class="pdf-viewport" :class="{ 'is-panning': isPanning }" ref="translationViewport" @wheel="handleWheel" @mousedown="handleMouseDown">
              <div class="page-container">
                <div class="page-transform">
                  <div class="page-layer" :style="{ width: scaledDisplayWidth + 'px', height: scaledDisplayHeight + 'px' }">
                    <img class="pdf-image" :src="pageImage" :width="scaledDisplayWidth" :height="scaledDisplayHeight" draggable="false" />
                    <div class="overlay-container">
                      <div
                        v-for="item in currentPageOverlays"
                        :key="String(item.block_id)"
                        class="overlay-block"
                        :style="getOverlayStyle(item.bbox, item.element_type)"
                      >
                        <div class="overlay-white"></div>
                        <div class="overlay-mask" :class="{ done: item.translated, failed: item.failed }">
                          <div v-if="item.failed" class="overlay-failed">失败</div>
                          <div v-else-if="!item.translated" class="overlay-loading">
                            <div class="spinner"></div>
                          </div>
                          <div v-else class="overlay-text" :class="getTextClass(item.element_type)">
                            {{ item.translated_text }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <PdfExportDialog
      v-model="exportDialogVisible"
      :pdf-names="[pdfName]"
      :use-dps="useDps"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button1 from '../elements/button/button1.vue'
import PdfExportDialog from '../components/PdfExportDialog.vue'
import { 
  generatePretranslation, 
  startTranslation, 
  getTranslationProgress,
  getPretranslationTasks,
  getTranslationResult,
  pauseTranslation,
  resumeTranslation,
  stopTranslation,
  getPDFPageImage,
  getPDFParsedData,
  getPDFDpsData
} from '../api/pdf'

const route = useRoute()
const router = useRouter()

// 路由参数
const pdfName = ref(route.query.pdfName || '')
const apiKey = ref(route.query.apiKey || '')
const useDps = ref(route.query.useDps === 'true')
const sourceLang = ref(route.query.sourceLang || 'en')
const targetLang = ref(route.query.targetLang || 'zh-CN')
const aggregateTitles = ref(route.query.aggregateTitles === 'true')
// 大模型厂商配置（缺省时后端回退 DeepSeek）
const llmProvider = ref(route.query.provider || '')
const llmBaseUrl = ref(route.query.baseUrl || '')
const llmModel = ref(route.query.model || '')
const maxConcurrent = ref(5)

const clampMaxConcurrent = (val) => {
  const n = Number(val)
  if (!Number.isFinite(n)) return 5
  return Math.max(1, Math.min(20, Math.floor(n)))
}

// 翻译状态
const isTranslating = ref(false)
const isCompleted = ref(false)
const isPaused = ref(false)
const isRefreshing = ref(false)  // 新增：刷新状态
const progressPercent = ref(0)
const progressMessage = ref('准备中...')
const currentCount = ref(0)
const totalCount = ref(0)
const currentTranslatingIndex = ref(-1)
const estimatedTime = ref('')

// 统计信息
const translationSuccess = ref(0)  // 翻译成功数
const translationFailed = ref(0)   // 翻译失败数
const distributionSuccess = ref(0) // 分配成功数
const distributionFailed = ref(0)  // 分配失败数

// 原文和译文数据
const originalTexts = ref([])  // 展开后的原文列表（用于显示）
const translatedTexts = ref([])  // 译文列表（与原文一一对应）
const tasksMap = ref({})  // task_id -> task 的映射

const parsedData = ref(null)
const dpsData = ref(null)
const totalPages = ref(0)
const currentPage = ref(0)
const pageImage = ref('')
const imageWidth = ref(0)
const imageHeight = ref(0)
const displayWidth = ref(0)
const displayHeight = ref(0)
const viewScale = ref(1.0)
const imageRenderScale = ref(3.0)

const pageImageCache = new Map()
const overlayStyleCache = new Map() // 缓存 overlay 样式计算结果
const originalViewport = ref(null)
const translationViewport = ref(null)

const scaledDisplayWidth = computed(() => Math.max(1, Math.floor(displayWidth.value * viewScale.value)))
const scaledDisplayHeight = computed(() => Math.max(1, Math.floor(displayHeight.value * viewScale.value)))

// SSE连接
let eventSource = null
let taskId = null
let zoomRenderTimer = null

const clamp = (val, min, max) => Math.max(min, Math.min(max, val))
const roundScale = (val) => Math.round(val * 100) / 100
const getDesiredRenderScale = (scale) => {
  const desired = clamp(3.0 * scale, 3.0, 6.0)
  return roundScale(desired)
}

const isPanning = ref(false)
let panState = null
let panListenersBound = false

const bindPanListeners = () => {
  if (panListenersBound) return
  window.addEventListener('mousemove', handleMouseMove, { passive: false })
  window.addEventListener('mouseup', handleMouseUp, { passive: false })
  panListenersBound = true
}

const unbindPanListeners = () => {
  if (!panListenersBound) return
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
  panListenersBound = false
}

// 状态类和文本
const statusClass = computed(() => {
  if (isCompleted.value) return 'completed'
  if (isPaused.value) return 'paused'
  if (isTranslating.value) return 'translating'
  return 'idle'
})

const statusText = computed(() => {
  if (isCompleted.value) return '翻译完成'
  if (isPaused.value) return '已暂停'
  if (isTranslating.value) return '翻译中'
  return '准备中'
})

// 元素类型标签映射
const typeLabels = {
  document_title: '文档标题',
  section_title: '章节标题',
  paragraph: '段落',
  list: '列表',
  display_formula: '公式',
  formula_caption: '公式标题',
  figure: '图片',
  figure_caption: '图片标题',
  table: '表格',
  table_caption: '表格标题',
  table_footnote: '表格注释'
}

const getTypeLabel = (type) => {
  return typeLabels[type] || type
}

// 初始化
onMounted(async () => {
  if (!pdfName.value) {
    window.$toast?.error('缺少PDF名称参数')
    router.back()
    return
  }

  maxConcurrent.value = clampMaxConcurrent(route.query.maxConcurrent)
  console.log('[Translation] 启动参数:', {
    pdfName: pdfName.value,
    useDps: useDps.value,
    sourceLang: sourceLang.value,
    targetLang: targetLang.value,
    aggregateTitles: aggregateTitles.value,
    maxConcurrent: maxConcurrent.value,
    provider: llmProvider.value || 'deepseek',
    model: llmModel.value || '-',
    hasApiKey: Boolean(apiKey.value)
  })

  await initTranslation()
})

const pythonPageSize = computed(() => {
  const page = parsedData.value?.pages?.[currentPage.value]
  const size = page?.page_size
  const width = typeof size?.width === 'number' ? size.width : null
  const height = typeof size?.height === 'number' ? size.height : null
  if (!width || !height) return null
  return { width, height }
})

const dpsPageSize = computed(() => {
  const pages = dpsData.value?.pages ?? dpsData.value?.raw?.pages
  if (!Array.isArray(pages)) return null
  const pageObj = pages.find(p => p?.page_index === currentPage.value) || pages[currentPage.value]
  const width = typeof pageObj?.width === 'number' ? pageObj.width : null
  const height = typeof pageObj?.height === 'number' ? pageObj.height : null
  if (!width || !height) return null
  return { width, height }
})

const refPageSize = computed(() => {
  return useDps.value ? dpsPageSize.value : pythonPageSize.value
})

const translatedByBlockId = computed(() => {
  const map = {}
  for (const t of translatedTexts.value) {
    if (!t) continue
    if (t.block_id !== undefined && t.block_id !== null) {
      map[String(t.block_id)] = t
    }
  }
  return map
})

const currentPageOverlays = computed(() => {
  const list = []
  const tMap = translatedByBlockId.value
  const currentPageNum = currentPage.value
  
  // 只处理当前页的元素，减少计算量
  for (const item of originalTexts.value) {
    if (item.page_num !== currentPageNum) continue
    const bbox = item.bbox
    if (!Array.isArray(bbox) || bbox.length < 4) continue
    const key = String(item.block_id)
    const translated = tMap[key]
    list.push({
      ...item,
      translated: Boolean(translated?.translated_text) || Boolean(item.translated),
      translated_text: translated?.translated_text || '',
      failed: Boolean(item.failed)
    })
  }
  return list
})

const loadViewerBaseData = async () => {
  if (useDps.value) {
    const resp = await getPDFDpsData(pdfName.value)
    dpsData.value = resp.data
    const pages = dpsData.value?.pages ?? dpsData.value?.raw?.pages
    totalPages.value = Array.isArray(pages) ? pages.length : 0
  } else {
    const resp = await getPDFParsedData(pdfName.value)
    parsedData.value = resp.data
    totalPages.value = parsedData.value?.total_pages ?? 0
  }
}

const getPageImageCacheKey = (pageNum, renderScale) => `${pageNum}@${renderScale}`

const loadPageImage = async (pageNum, renderScale = imageRenderScale.value) => {
  const cacheKey = getPageImageCacheKey(pageNum, renderScale)
  const cached = pageImageCache.get(cacheKey)
  if (cached) {
    pageImage.value = cached.image
    imageWidth.value = cached.width
    imageHeight.value = cached.height
    imageRenderScale.value = cached.renderScale
    calculateDisplaySize()
    return
  }

  const resp = await getPDFPageImage(pdfName.value, pageNum, renderScale)
  const payload = resp?.data
  if (payload?.image) {
    const item = {
      image: payload.image,
      width: payload.width,
      height: payload.height,
      renderScale
    }
    pageImageCache.set(cacheKey, item)
    pageImage.value = item.image
    imageWidth.value = item.width
    imageHeight.value = item.height
    imageRenderScale.value = item.renderScale
    calculateDisplaySize()
    console.log('[Translation] 页面图片已加载:', {
      pageNum,
      renderScale,
      pixWidth: item.width,
      pixHeight: item.height
    })
  }
}

// 计算显示尺寸（根据容器宽度自适应）
const calculateDisplaySize = () => {
  if (!imageWidth.value || !imageHeight.value) return
  
  // 获取容器宽度（半个屏幕减去padding和边距）
  const containerWidth = originalViewport.value?.clientWidth || window.innerWidth / 2
  const availableWidth = containerWidth - 40 // 减去padding
  
  // 根据容器宽度计算显示尺寸
  const aspectRatio = imageHeight.value / imageWidth.value
  displayWidth.value = Math.floor(availableWidth)
  displayHeight.value = Math.floor(availableWidth * aspectRatio)
}

// 左右滚动同步 - 使用wheel事件实现流畅同步
const scheduleEnsureResolutionForScale = (scale) => {
  const desiredRenderScale = getDesiredRenderScale(scale)
  if (desiredRenderScale === imageRenderScale.value) return
  if (zoomRenderTimer) clearTimeout(zoomRenderTimer)
  zoomRenderTimer = setTimeout(async () => {
    try {
      const latestDesired = getDesiredRenderScale(viewScale.value)
      if (latestDesired === imageRenderScale.value) return
      console.log('[Translation] 触发高清重渲染:', {
        page: currentPage.value,
        viewScale: viewScale.value,
        from: imageRenderScale.value,
        to: latestDesired
      })
      await loadPageImage(currentPage.value, latestDesired)
    } catch (e) {
      console.error('[Translation] 高清重渲染失败:', e)
    }
  }, 180)
}

const setScaleWithAnchor = async (newScale, e) => {
  const nextScale = clamp(roundScale(newScale), 0.5, 5.0)
  if (nextScale === viewScale.value) return

  const sourceViewport = e?.currentTarget || originalViewport.value
  if (!sourceViewport) return
  const rect = sourceViewport?.getBoundingClientRect?.()
  const hasClientPoint = typeof e?.clientX === 'number' && typeof e?.clientY === 'number'
  const clientX = hasClientPoint ? e.clientX : (rect ? rect.left + rect.width / 2 : 0)
  const clientY = hasClientPoint ? e.clientY : (rect ? rect.top + rect.height / 2 : 0)
  const offsetX = rect ? clientX - rect.left : 0
  const offsetY = rect ? clientY - rect.top : 0

  const oldScale = viewScale.value
  const baseX = sourceViewport ? (sourceViewport.scrollLeft + offsetX) / oldScale : 0
  const baseY = sourceViewport ? (sourceViewport.scrollTop + offsetY) / oldScale : 0

  viewScale.value = nextScale
  overlayStyleCache.clear()
  await nextTick()

  const nextLeft = baseX * nextScale - offsetX
  const nextTop = baseY * nextScale - offsetY

  if (originalViewport.value) {
    originalViewport.value.scrollLeft = nextLeft
    originalViewport.value.scrollTop = nextTop
  }
  if (translationViewport.value) {
    translationViewport.value.scrollLeft = nextLeft
    translationViewport.value.scrollTop = nextTop
  }

  scheduleEnsureResolutionForScale(nextScale)
  console.log('[Translation] 缩放更新:', { from: oldScale, to: nextScale, anchor: { offsetX, offsetY } })
}

const handleWheel = (e) => {
  if (e.ctrlKey) {
    e.preventDefault()
    const direction = e.deltaY < 0 ? 1 : -1
    const step = 0.12
    const next = viewScale.value + direction * step
    setScaleWithAnchor(next, e)
    return
  }

  e.preventDefault()

  const deltaX = e.deltaX
  const deltaY = e.deltaY

  if (originalViewport.value) {
    originalViewport.value.scrollTop += deltaY
    originalViewport.value.scrollLeft += deltaX
  }

  if (translationViewport.value) {
    translationViewport.value.scrollTop += deltaY
    translationViewport.value.scrollLeft += deltaX
  }
}

const handleMouseDown = (e) => {
  if (!e.ctrlKey) return
  if (e.button !== 0) return
  if (!originalViewport.value || !translationViewport.value) return

  e.preventDefault()
  isPanning.value = true
  panState = {
    startX: e.clientX,
    startY: e.clientY,
    startLeft: originalViewport.value.scrollLeft,
    startTop: originalViewport.value.scrollTop
  }
  bindPanListeners()
  console.log('[Translation] 开始拖拽平移:', panState)
}

const handleMouseMove = (e) => {
  if (!isPanning.value || !panState) return
  e.preventDefault()

  const dx = e.clientX - panState.startX
  const dy = e.clientY - panState.startY
  const nextLeft = panState.startLeft - dx
  const nextTop = panState.startTop - dy

  if (originalViewport.value) {
    originalViewport.value.scrollLeft = nextLeft
    originalViewport.value.scrollTop = nextTop
  }
  if (translationViewport.value) {
    translationViewport.value.scrollLeft = nextLeft
    translationViewport.value.scrollTop = nextTop
  }
}

const handleMouseUp = (e) => {
  if (!isPanning.value) return
  e.preventDefault()
  isPanning.value = false
  panState = null
  unbindPanListeners()
  console.log('[Translation] 结束拖拽平移')
}

const goPrevPage = async () => {
  if (currentPage.value <= 0) return
  // 清空样式缓存（页面变化时）
  overlayStyleCache.clear()
  currentPage.value -= 1
  await loadPageImage(currentPage.value)
  // 预加载前一页
  preloadAdjacentPages()
}

const goNextPage = async () => {
  if (!totalPages.value || currentPage.value >= totalPages.value - 1) return
  // 清空样式缓存（页面变化时）
  overlayStyleCache.clear()
  currentPage.value += 1
  await loadPageImage(currentPage.value)
  // 预加载后一页
  preloadAdjacentPages()
}

// 预加载相邻页面（提前加载，减少等待时间）
const preloadAdjacentPages = () => {
  // 不阻塞当前操作，异步预加载
  setTimeout(() => {
    // 预加载下一页
    if (currentPage.value + 1 < totalPages.value) {
      loadPageImageSilent(currentPage.value + 1)
    }
    // 预加载上一页
    if (currentPage.value - 1 >= 0) {
      loadPageImageSilent(currentPage.value - 1)
    }
  }, 100)
}

// 静默加载页面（仅缓存，不更新显示）
const loadPageImageSilent = async (pageNum) => {
  const cacheKey = getPageImageCacheKey(pageNum, 3.0)
  const cached = pageImageCache.get(cacheKey)
  if (cached) return // 已缓存，无需加载

  try {
    const resp = await getPDFPageImage(pdfName.value, pageNum, 3.0)
    const payload = resp?.data
    if (payload?.image) {
      const item = {
        image: payload.image,
        width: payload.width,
        height: payload.height,
        renderScale: 3.0
      }
      pageImageCache.set(cacheKey, item)
    }
  } catch (error) {
    // 静默失败，不影响用户操作
    console.log(`预加载页面 ${pageNum} 失败:`, error.message)
  }
}

const zoomIn = () => {
  setScaleWithAnchor(viewScale.value + 0.1)
}

const zoomOut = () => {
  setScaleWithAnchor(viewScale.value - 0.1)
}

const getOverlayStyle = (bbox, elementType) => {
  if (!Array.isArray(bbox) || bbox.length < 4) return {}
  const refSize = refPageSize.value
  if (!refSize?.width || !refSize?.height || !scaledDisplayWidth.value || !scaledDisplayHeight.value) return {}

  // 使用缓存减少重复计算
  const cacheKey = `${bbox.join(',')}_${scaledDisplayWidth.value}_${scaledDisplayHeight.value}_${refSize.width}_${refSize.height}_${elementType}`
  const cached = overlayStyleCache.get(cacheKey)
  if (cached) return cached

  const [x0, y0, x1, y1] = bbox
  const scaleX = scaledDisplayWidth.value / refSize.width
  const scaleY = scaledDisplayHeight.value / refSize.height
  
  // 计算实际高度
  let actualHeight = (y1 - y0) * scaleY
  
  // 获取该元素类型的最小高度
  const minHeight = getMinHeight(elementType)
  
  // 如果实际高度小于最小高度，则扩展
  if (actualHeight < minHeight) {
    actualHeight = minHeight
  }
  
  const style = {
    left: `${x0 * scaleX}px`,
    top: `${y0 * scaleY}px`,
    width: `${(x1 - x0) * scaleX}px`,
    height: `${actualHeight}px`
  }
  
  overlayStyleCache.set(cacheKey, style)
  return style
}

// 根据元素类型返回CSS类名
const getTextClass = (elementType) => {
  // 论文标题
  if (elementType === 'document_title') {
    return 'text-document-title'
  }
  
  // 章节标题（一级）
  if (elementType === 'section_title') {
    return 'text-section-title'
  }
  
  // 二级标题
  if (elementType === 'section_title_2') {
    return 'text-section-title-2'
  }
  
  // 三级标题
  if (elementType === 'section_title_3') {
    return 'text-section-title-3'
  }
  
  // 图表标题（粉色，段落字号）
  if (elementType === 'figure_caption' || elementType === 'table_caption') {
    return 'text-figure-table-caption'
  }
  
  // 公式标题（保持原样）
  if (elementType === 'formula_caption') {
    return 'text-formula-caption'
  }
  
  return 'text-paragraph'
}

// 根据元素类型获取最小高度（单位：px）
const getMinHeight = (elementType) => {
  const zoom = viewScale.value || 1
  // 考虑 padding (4px 上下 = 8px) + 行高
  if (elementType === 'document_title') {
    return Math.round(32 * zoom)  // 18px * 1.4 (行高) + 8px (padding) ≈ 33.2，取32
  }
  // 一级标题
  if (elementType === 'section_title') {
    return Math.round(28 * zoom)  // 14.4px * 1.4 + 8px ≈ 28.16
  }
  // 二级标题
  if (elementType === 'section_title_2') {
    return Math.round(27 * zoom)  // 13.2px * 1.4 + 8px ≈ 26.48
  }
  // 三级标题
  if (elementType === 'section_title_3') {
    return Math.round(26 * zoom)  // 12.6px * 1.4 + 8px ≈ 25.64
  }
  // 公式标题（比段落略大）
  if (elementType === 'formula_caption') {
    return Math.round(28 * zoom)  // 14.4px * 1.4 + 8px ≈ 28.16
  }
  // 图表标题（与段落同大小）
  if (elementType === 'figure_caption' || elementType === 'table_caption') {
    return Math.round(25 * zoom)  // 12px * 1.4 + 8px ≈ 24.8
  }
  return Math.round(25 * zoom)  // 12px * 1.4 + 8px ≈ 24.8，取25
}

// 初始化翻译
const initTranslation = async () => {
  try {
    // 1. 生成预翻译文件（如果不存在）
    progressMessage.value = '生成预翻译文件...'
    const prepareResult = await generatePretranslation(pdfName.value, {
      source_lang: sourceLang.value,
      target_lang: targetLang.value,
      aggregate_titles: aggregateTitles.value,
      use_dps: useDps.value,
      force: false
    })

    if (prepareResult.code !== 200) {
      throw new Error(prepareResult.message || '生成预翻译文件失败')
    }

    // 2. 获取预翻译任务清单（加载原文数据）
    progressMessage.value = '加载原文数据...'
    const tasksResult = await getPretranslationTasks(pdfName.value, useDps.value)
    
    if (tasksResult.code !== 200) {
      throw new Error(tasksResult.message || '加载预翻译任务失败')
    }

    // 解析任务数据
    const pretransData = tasksResult.data
    const tasks = pretransData.translation_tasks || []
    
    // 构建 task_id -> task 的映射
    const taskMap = {}
    for (const task of tasks) {
      taskMap[task.task_id] = task
    }
    tasksMap.value = taskMap
    
    // 将聚合任务展开为原文列表
    const expandedTasks = []
    for (const task of tasks) {
      if (task.is_aggregated && task.aggregated_blocks) {
        // 聚合任务：展开为多个原文项
        for (const block of task.aggregated_blocks) {
          expandedTasks.push({
            task_id: task.task_id,
            page_num: block.page_num,
            block_id: block.block_id,
            element_type: block.element_type,
            source_text: block.text,
            bbox: block.bbox,
            reading_order: block.reading_order,
            is_part_of_aggregation: true,
            parent_task_id: task.task_id
          })
        }
      } else {
        // 独立任务
        expandedTasks.push({
          task_id: task.task_id,
          page_num: task.page_num,
          block_id: task.block_id,
          element_type: task.element_type,
          source_text: task.source_text || task.aggregated_text,
          bbox: task.bbox,
          reading_order: task.reading_order,
          is_part_of_aggregation: false
        })
      }
    }
    
    originalTexts.value = expandedTasks
    // 初始化译文列表，与原文一一对应
    translatedTexts.value = expandedTasks.map(() => null)
    totalCount.value = tasks.length  // 总任务数（不是展开后的数量）

    progressMessage.value = '加载PDF页面...'
    await loadViewerBaseData()
    currentPage.value = 0
    await loadPageImage(0)
    // 预加载第一页和第二页
    preloadAdjacentPages()

    // 【关键修复】3. 检查是否已有翻译结果
    progressMessage.value = '检查翻译状态...'
    let hasExistingTranslation = false
    try {
      const existingResult = await getTranslationResult(pdfName.value, useDps.value)
      
      if (existingResult.code === 200 && existingResult.data) {
        const translationData = existingResult.data
        const translatedTasks = translationData.translation_tasks || []
        
        // 只要有翻译数据就加载（不管是否全部完成）
        if (translatedTasks.length > 0) {
          console.log('检测到已有翻译结果，加载现有数据')
          loadExistingTranslations(translatedTasks)
          hasExistingTranslation = true
          
          // 更新统计信息
          const stats = translationData.statistics || {}
          translationSuccess.value = stats.translation_success || 0
          translationFailed.value = stats.translation_failed || 0
          distributionSuccess.value = stats.distribution_success || 0
          distributionFailed.value = stats.distribution_failed || 0
          
          // 检查是否所有任务都已翻译完成
          const allTranslated = translatedTasks.every(t => 
            t.translation_status === 'success' || t.translation_status === 'failed'
          )
          
          if (allTranslated) {
            // 标记为完成状态
            isTranslating.value = false
            isCompleted.value = true
            progressPercent.value = 100
            progressMessage.value = '翻译已完成'
            currentCount.value = totalCount.value
            
            window.$toast?.success('翻译结果加载完成')
            return  // 已完成，不需要重新翻译
          } else {
            // 部分完成，计算进度
            const completedCount = translatedTasks.filter(t => 
              t.translation_status === 'success' || t.translation_status === 'failed'
            ).length
            currentCount.value = completedCount
            progressPercent.value = Math.round((completedCount / totalCount.value) * 100)
            progressMessage.value = `已加载 ${completedCount}/${totalCount.value} 个翻译`
          }
        }
      }
    } catch (err) {
      console.log('未找到已有翻译结果', err.message)
    }

    // 4. 如果没有apiKey但有翻译结果，停在这里
    if (!apiKey.value) {
      if (hasExistingTranslation) {
        window.$toast?.success('翻译结果加载完成（只读模式）')
        isTranslating.value = false
        return
      } else {
        window.$toast?.error('无翻译结果且未提供API Key，无法开始翻译')
        router.back()
        return
      }
    }

    // 5. 开始新翻译（需要apiKey）
    progressMessage.value = '创建翻译任务...'
    const translateResult = await startTranslation({
      pdf_name: pdfName.value,
      api_key: apiKey.value,
      use_dps: useDps.value,
      max_concurrent: maxConcurrent.value,
      enable_distribution: true,
      provider: llmProvider.value || undefined,
      base_url: llmBaseUrl.value || undefined,
      model: llmModel.value || undefined
    })

    if (translateResult.code !== 200) {
      throw new Error(translateResult.message || '创建翻译任务失败')
    }

    taskId = translateResult.data.task_id
    if (!taskId) {
      throw new Error('未获取到task_id')
    }

    // 6. 连接SSE接收实时进度
    connectSSE(taskId)
    isTranslating.value = true

  } catch (error) {
    console.error('初始化翻译失败:', error)
    window.$toast?.error(error.message || '初始化翻译失败')
    router.back()
  }
}

// 加载已有的翻译结果
const loadExistingTranslations = (translatedTasks) => {
  console.log(`加载 ${translatedTasks.length} 个已翻译任务`)
  
  for (const task of translatedTasks) {
    if (task.translation_status !== 'success') {
      continue  // 跳过翻译失败的任务
    }
    
    if (task.is_aggregated && task.aggregated_blocks) {
      // 聚合任务：从 aggregated_blocks 中获取译文
      for (const block of task.aggregated_blocks) {
        const blockIndex = originalTexts.value.findIndex(
          item => item.block_id === block.block_id && item.task_id === task.task_id
        )
        
        if (blockIndex !== -1 && block.translated_text) {
          originalTexts.value[blockIndex].translated = true
          translatedTexts.value[blockIndex] = {
            task_id: task.task_id,
            block_id: block.block_id,
            element_type: block.element_type,
            page_num: block.page_num,
            translated_text: block.translated_text,
            is_part_of_aggregation: true
          }
        }
      }
    } else {
      // 单个任务：直接使用 translated_text
      const sourceIndex = originalTexts.value.findIndex(item => item.task_id === task.task_id)
      
      if (sourceIndex !== -1 && task.translated_text) {
        originalTexts.value[sourceIndex].translated = true
        translatedTexts.value[sourceIndex] = {
          task_id: task.task_id,
          block_id: originalTexts.value[sourceIndex].block_id,
          element_type: task.element_type,
          page_num: task.page_num,
          translated_text: task.translated_text,
          is_part_of_aggregation: false
        }
      }
    }
  }
  
  const loadedCount = translatedTexts.value.filter(t => t !== null).length
  console.log(`成功加载 ${loadedCount} 段译文`)
}

// 连接SSE
const connectSSE = (tid) => {
  eventSource?.close()
  eventSource = new EventSource(`http://localhost:8000/api/v1/translation/progress/${tid}`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      progressPercent.value = Math.max(0, Math.min(100, Math.round(Number(data.progress || 0))))
      currentCount.value = Number(data.current || 0)
      totalCount.value = Number(data.total || 0)
      progressMessage.value = data.message || '翻译中...'

      // 更新统计信息
      if (data.result && data.result.task_id) {
        const result = data.result
        const status = result.status
        
        if (data.phase === 'translation') {
          if (status === 'success') {
            // 翻译成功（后端已计数，这里只用于显示）
          } else if (status === 'failed') {
            const task = tasksMap.value[result.task_id]
            if (task?.is_aggregated) {
              originalTexts.value.forEach(item => {
                if (item.task_id === result.task_id) {
                  item.failed = true
                  item.error = result.error
                }
              })
            } else {
              const failedIndex = originalTexts.value.findIndex(item => item.task_id === result.task_id)
              if (failedIndex !== -1) {
                originalTexts.value[failedIndex].failed = true
                originalTexts.value[failedIndex].error = result.error
              }
            }
          }
        } else if (data.phase === 'distribution') {
          if (status === 'success') {
            // 分配成功
          } else if (status === 'failed') {
            // 分配失败：标记聚合任务的所有块为失败
            const task = tasksMap.value[result.task_id]
            if (task && task.is_aggregated) {
              originalTexts.value.forEach(item => {
                if (item.task_id === result.task_id) {
                  item.failed = true
                  item.error = result.error || '分配失败'
                }
              })
            }
          }
        }
      }
      
      // 从后端返回的统计数据更新前端显示
      if (data.translation_success !== undefined) {
        translationSuccess.value = data.translation_success
      }
      if (data.translation_failed !== undefined) {
        translationFailed.value = data.translation_failed
      }
      if (data.distribution_success !== undefined) {
        distributionSuccess.value = data.distribution_success
      }
      if (data.distribution_failed !== undefined) {
        distributionFailed.value = data.distribution_failed
      }

      // 更新当前翻译索引
      if (data.current_task_id) {
        const index = originalTexts.value.findIndex(item => item.task_id === data.current_task_id)
        if (index !== -1) {
          currentTranslatingIndex.value = index
        }
      }

      // 处理单条翻译结果
      if (data.result && data.result.task_id) {
        const result = data.result
        const task = tasksMap.value[result.task_id]
        
        if (task && task.is_aggregated) {
          // 聚合任务：需要分配译文到各个 block
          const distributedResults = result.distributed_results || []
          
          for (const distResult of distributedResults) {
            // 找到对应的 block_id 在 originalTexts 中的位置
            const blockIndex = originalTexts.value.findIndex(
              item => item.block_id === distResult.block_id && item.task_id === result.task_id
            )
            
            if (blockIndex !== -1) {
              // 标记为已翻译
              originalTexts.value[blockIndex].translated = true
              
              // 将译文放入对应位置
              translatedTexts.value[blockIndex] = {
                task_id: result.task_id,
                block_id: distResult.block_id,
                element_type: originalTexts.value[blockIndex].element_type,
                page_num: distResult.page_num,
                translated_text: distResult.translated_text,
                is_part_of_aggregation: true
              }
            }
          }
        } else {
          // 独立任务：直接匹配
          const sourceIndex = originalTexts.value.findIndex(item => item.task_id === result.task_id)
          if (sourceIndex !== -1) {
            originalTexts.value[sourceIndex].translated = true
            translatedTexts.value[sourceIndex] = {
              task_id: result.task_id,
              block_id: originalTexts.value[sourceIndex].block_id,
              element_type: originalTexts.value[sourceIndex].element_type,
              page_num: originalTexts.value[sourceIndex].page_num,
              translated_text: result.translated_text,
              is_part_of_aggregation: false
            }
          }
        }
      }

      // 处理完成
      if (data.stage === 'completed') {
        isTranslating.value = false
        isCompleted.value = true
        currentTranslatingIndex.value = -1
        
        // 显示完成消息，包含统计信息
        const successCount = translationSuccess.value
        const failedCount = translationFailed.value
        if (failedCount > 0) {
          window.$toast?.warning(`翻译完成！成功: ${successCount}, 失败: ${failedCount}`)
        } else {
          window.$toast?.success(`翻译完成！全部成功: ${successCount}`)
        }
        
        eventSource?.close()
        eventSource = null
      } else if (data.stage === 'error') {
        isTranslating.value = false
        window.$toast?.error(data.message || '翻译失败')
        eventSource?.close()
        eventSource = null
      }
    } catch (e) {
      console.error('[Translation SSE] 解析数据失败:', e)
    }
  }

  eventSource.onerror = (error) => {
    console.error('[Translation SSE] 连接错误:', error)
    eventSource?.close()
    eventSource = null
    if (isTranslating.value) {
      progressMessage.value = '推送连接中断，翻译仍在后台进行'
    }
  }
}

// 返回
const handleBack = () => {
  if (isTranslating.value) {
    if (!confirm('翻译正在进行中，确定要离开吗？')) {
      return
    }
  }
  eventSource?.close()
  router.back()
}

// 暂停翻译
const handlePause = () => {
  if (!isTranslating.value) {
    return
  }
  
  // 关闭SSE连接（后端任务继续执行，前端停止接收进度）
  eventSource?.close()
  eventSource = null
  
  isPaused.value = true
  isTranslating.value = false
  
  window.$toast?.info('已暂停进度更新，翻译任务仍在后台继续执行')
  console.log('翻译已暂停（SSE连接关闭）')
}

// 继续翻译
const handleResume = async () => {
  if (!isPaused.value || !taskId) {
    return
  }
  
  try {
    // 1. 先从翻译结果文件加载已完成的任务
    progressMessage.value = '正在同步翻译进度...'
    const existingResult = await getTranslationResult(pdfName.value, useDps.value)
    
    if (existingResult.code === 200 && existingResult.data) {
      const translationData = existingResult.data
      const translatedTasks = translationData.translation_tasks || []
      
      // 加载已完成的译文
      loadExistingTranslations(translatedTasks)
      
      // 更新统计信息
      const stats = translationData.statistics || {}
      translationSuccess.value = stats.translation_success || 0
      translationFailed.value = stats.translation_failed || 0
      distributionSuccess.value = stats.distribution_success || 0
      distributionFailed.value = stats.distribution_failed || 0
      
      // 检查是否已全部完成
      const allCompleted = translatedTasks.every(t => 
        t.translation_status === 'success' || t.translation_status === 'failed'
      )
      
      if (allCompleted) {
        // 翻译已全部完成
        isPaused.value = false
        isCompleted.value = true
        isTranslating.value = false
        progressPercent.value = 100
        progressMessage.value = '翻译已完成'
        currentCount.value = totalCount.value
        window.$toast?.success('翻译已完成！')
        return
      }
    }
    
    // 2. 重新连接SSE继续接收进度
    connectSSE(taskId)
    isPaused.value = false
    isTranslating.value = true
    progressMessage.value = '继续翻译中...'
    
    window.$toast?.success('已恢复进度更新')
    console.log('翻译已继续（SSE重新连接）')
    
  } catch (error) {
    console.error('恢复翻译失败:', error)
    window.$toast?.error('恢复翻译失败: ' + error.message)
  }
}

// 停止翻译
const handleStop = async () => {
  if (!taskId) {
    return
  }
  
  if (!confirm('确定要停止翻译吗？已翻译的进度将保留。')) {
    return
  }
  
  try {
    // 调用后端API停止翻译
    const result = await stopTranslation(taskId)
    
    if (result.code === 200) {
      eventSource?.close()
      eventSource = null
      
      isTranslating.value = false
      isPaused.value = false
      progressMessage.value = '已停止'
      
      window.$toast?.info('已停止翻译，进度已保存')
      console.log('翻译已停止')
    } else {
      throw new Error(result.message || '停止失败')
    }
  } catch (error) {
    console.error('停止翻译失败:', error)
    window.$toast?.error('停止失败: ' + error.message)
  }
}

const exportDialogVisible = ref(false)

// 导出结果
const handleExport = () => {
  exportDialogVisible.value = true
}

// 刷新翻译结果
const handleRefresh = async () => {
  if (isRefreshing.value) {
    return  // 防止重复刷新
  }
  
  isRefreshing.value = true
  
  try {
    console.log('刷新翻译结果...')
    
    // 1. 重新加载翻译结果
    const existingResult = await getTranslationResult(pdfName.value, useDps.value)
    
    if (existingResult.code === 200 && existingResult.data) {
      const translationData = existingResult.data
      const translatedTasks = translationData.translation_tasks || []
      
      if (translatedTasks.length > 0) {
        // 加载已完成的译文
        loadExistingTranslations(translatedTasks)
        
        // 更新统计信息
        const stats = translationData.statistics || {}
        translationSuccess.value = stats.translation_success || 0
        translationFailed.value = stats.translation_failed || 0
        distributionSuccess.value = stats.distribution_success || 0
        distributionFailed.value = stats.distribution_failed || 0
        
        // 检查是否所有任务都已翻译完成
        const allTranslated = translatedTasks.every(t => 
          t.translation_status === 'success' || t.translation_status === 'failed'
        )
        
        if (allTranslated) {
          // 标记为完成状态
          isTranslating.value = false
          isCompleted.value = true
          progressPercent.value = 100
          progressMessage.value = '翻译已完成'
          currentCount.value = totalCount.value
          window.$toast?.success('刷新成功！翻译已完成')
        } else {
          // 部分完成，计算进度
          const completedCount = translatedTasks.filter(t => 
            t.translation_status === 'success' || t.translation_status === 'failed'
          ).length
          currentCount.value = completedCount
          progressPercent.value = Math.round((completedCount / totalCount.value) * 100)
          progressMessage.value = `已加载 ${completedCount}/${totalCount.value} 个翻译`
          window.$toast?.success(`刷新成功！进度: ${completedCount}/${totalCount.value}`)
        }
      } else {
        window.$toast?.info('暂无翻译结果')
      }
    } else {
      window.$toast?.warning('未找到翻译结果')
    }
    
  } catch (error) {
    console.error('刷新翻译结果失败:', error)
    window.$toast?.error('刷新失败: ' + error.message)
  } finally {
    isRefreshing.value = false
  }
}

// 监听窗口大小变化，重新计算显示尺寸
const handleResize = () => {
  calculateDisplaySize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  unbindPanListeners()
  eventSource?.close()
  eventSource = null
})
</script>

<style scoped lang="scss">
.translation-execution {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

// 主内容区域
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 16px 20px;
  gap: 12px;
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e4e7ed;
  border-radius: 14px;
  padding: 10px 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.page-controls,
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
  background: white;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mini-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.mini-btn:hover:not(:disabled) {
  border-color: #409eff;
  color: #409eff;
  background: #f5f7fa;
}

.page-indicator,
.zoom-indicator {
  font-size: 13px;
  color: #606266;
  min-width: 110px;
  text-align: center;
}

.viewer-panels {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  overflow: hidden;
}

.pdf-panel .panel-content {
  padding: 0;
}

.pdf-viewer {
  height: 100%;
  overflow: hidden;
}

.pdf-viewport {
  width: 100%;
  height: 100%;
  overflow: auto;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  padding: 20px;
  cursor: default;
  
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f0f2f5;
  }

  &::-webkit-scrollbar-thumb {
    background: #c0c4cc;
    border-radius: 4px;

    &:hover {
      background: #909399;
    }
  }
}

.pdf-viewport.is-panning {
  cursor: grabbing;
}

.page-container {
  display: block;
  width: max-content;
  flex: 0 0 auto;
  margin: 0 auto;
}

.page-transform {
  transform-origin: top center;
  display: inline-block;
  will-change: transform;
}

.page-layer {
  position: relative;
  contain: layout style paint;
}

.pdf-image {
  display: block;
  width: 100%;
  height: auto;
  user-select: none;
  pointer-events: none;
}

.overlay-container {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  contain: layout style;
}

.overlay-block {
  position: absolute;
  will-change: transform;
  contain: layout style paint;
}

.overlay-white {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: #ffffff;
}

.overlay-mask {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(64, 158, 255, 0.35);
  box-sizing: border-box;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.overlay-mask.done {
  background: transparent;
  border-color: rgba(0, 0, 0, 0.08);
}

.overlay-mask.failed {
  background: rgba(255, 0, 0, 0.06);
  border-color: rgba(245, 108, 108, 0.8);
}

.overlay-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.overlay-loading .spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #409eff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.overlay-text {
  width: 100%;
  height: 100%;
  padding: 4px 6px;
  text-align: left;
  line-height: 1.4;
  word-break: break-word;
  white-space: pre-wrap;
  overflow: hidden;
  contain: layout style;
}

.translation-panel {
  --overlay-zoom-scale: 1;
  --overlay-font-paragraph-base: clamp(10px, 0.75vw, 16px);
  --overlay-font-paragraph: calc(var(--overlay-font-paragraph-base) * var(--overlay-zoom-scale));
  --overlay-font-document-title: calc(var(--overlay-font-paragraph) * 1.5);
  --overlay-font-section-title: calc(var(--overlay-font-paragraph) * 1.2);
  --overlay-font-section-title-2: calc(var(--overlay-font-paragraph) * 1.1);
  --overlay-font-section-title-3: calc(var(--overlay-font-paragraph) * 1.05);
  --overlay-font-figure-table-caption: var(--overlay-font-paragraph);
  --overlay-font-formula-caption: calc(var(--overlay-font-paragraph) * 1.2);
  --overlay-font-failed: var(--overlay-font-paragraph);
}

@supports (font-size: 1cqw) {
  .translation-panel {
    container-type: inline-size;
    --overlay-font-paragraph-base: clamp(10px, 1.5cqw, 16px);
  }
}

// 段落字体样式（基础字体）
.overlay-text.text-paragraph {
  font-size: var(--overlay-font-paragraph, 12px);
  color: #000000;
  font-weight: 400;
}

// 论文标题样式（暗金色，最大字号）
.overlay-text.text-document-title {
  font-size: var(--overlay-font-document-title, 18px); /* 12px * 1.5 = 18px */
  color: #b8860b; /* 暗金色 DarkGoldenrod */
  font-weight: 700;
}

// 一级标题样式（深蓝色，比段落大1.2個）
.overlay-text.text-section-title {
  font-size: var(--overlay-font-section-title, 14.4px); /* 12px * 1.2 = 14.4px */
  color: #1e3a8a; /* 深蓝色 */
  font-weight: 600;
}

// 二级标题样式（深红色，比段落大1.1倍）
.overlay-text.text-section-title-2 {
  font-size: var(--overlay-font-section-title-2, 13.2px); /* 12px * 1.1 = 13.2px */
  color: #991b1b; /* 深红色 */
  font-weight: 600;
}

// 三级标题样式（深紫色，比段落大1.05倍）
.overlay-text.text-section-title-3 {
  font-size: var(--overlay-font-section-title-3, 12.6px); /* 12px * 1.05 = 12.6px */
  color: #6b21a8; /* 深紫色 */
  font-weight: 600;
}

// 图表标题样式（粉色，与段落同大小）
.overlay-text.text-figure-table-caption {
  font-size: var(--overlay-font-figure-table-caption, 12px); /* 与段落相同 */
  color: #ec4899; /* 粉色 */
  font-weight: 500;
}

// 公式标题样式（深绿色，比段落大1.2倍）
.overlay-text.text-formula-caption {
  font-size: var(--overlay-font-formula-caption, 14.4px); /* 12px * 1.2 = 14.4px */
  color: #047857; /* 深绿色 */
  font-weight: 600;
}

.overlay-failed {
  color: #f56c6c;
  font-size: var(--overlay-font-failed, 12px);
  font-weight: 600;
}

// 顶部导航栏
.top-navbar {
  height: 72px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;

  .navbar-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .navbar-title {
    h2 {
      font-size: 20px;
      font-weight: 600;
      color: #2c3e50;
      margin: 0 0 4px 0;
    }

    .subtitle {
      font-size: 13px;
      color: #909399;
    }
  }

  .navbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .translate-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      animation: pulse 2s ease-in-out infinite;
    }

    &.idle {
      background: #f0f0f0;
      color: #909399;
      .status-dot {
        background: #909399;
      }
    }

    &.translating {
      background: #e1f3ff;
      color: #409eff;
      .status-dot {
        background: #409eff;
      }
    }

    &.paused {
      background: #fdf6ec;
      color: #e6a23c;
      .status-dot {
        background: #e6a23c;
        animation: none;
      }
    }

    &.completed {
      background: #f0f9ff;
      color: #67c23a;
      .status-dot {
        background: #67c23a;
        animation: none;
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.4;
      }
    }
  }

  .nav-btn {
    width: 40px;
    height: 40px;
    border: 1px solid #dcdfe6;
    background: white;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    color: #606266;

    &:hover:not(:disabled) {
      background: #f5f7fa;
      border-color: #409eff;
      color: #409eff;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    // 刷新按钮样式
    &.refresh-btn {
      svg.spinning {
        animation: spin 0.8s linear infinite;
      }
    }

    &.back-btn {
      width: auto;
      padding: 0 16px;
      gap: 8px;

      &:hover {
        border-color: #c0c4cc;
        color: #2c3e50;
      }
    }

    &.export-btn {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      border: none;
      color: white;

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
      }
    }
  }
}

// 进度信息栏
.progress-bar {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 16px 24px;
  flex-shrink: 0;

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    .progress-text {
      font-size: 14px;
      font-weight: 500;
      color: #606266;
    }

    .progress-count {
      font-size: 14px;
      font-weight: 600;
      color: #409eff;
    }
  }

  .progress-line {
    height: 8px;
    background: #f0f2f5;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
      border-radius: 4px;
      transition: width 0.3s ease;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: shimmer 1.5s infinite;
      }
    }

    @keyframes shimmer {
      0% {
        transform: translateX(-100%);
      }
      100% {
        transform: translateX(100%);
      }
    }
  }

  .progress-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #909399;
    
    .translation-stats {
      display: flex;
      gap: 16px;
      
      .stat-item {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 500;
        
        svg {
          flex-shrink: 0;
        }
        
        &.success {
          color: #67c23a;
          background: #f0f9ff;
        }
        
        &.failed {
          color: #f56c6c;
          background: #fef0f0;
        }
      }
    }
  }
}

// 主内容区域
.main-content {
  flex: 1;
  display: flex;
  gap: 1px;
  background: #e4e7ed;
  overflow: hidden;
}

.content-panel {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .panel-header {
    height: 56px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 20px;
    background: #fafbfc;
    flex-shrink: 0;

    svg {
      color: #409eff;
    }

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #2c3e50;
      margin: 0;
      flex: 1;
    }

    .item-count {
      font-size: 13px;
      color: #909399;
      background: #f0f2f5;
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 500;
    }
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f0f2f5;
    }

    &::-webkit-scrollbar-thumb {
      background: #c0c4cc;
      border-radius: 3px;

      &:hover {
        background: #909399;
      }
    }
  }

  .empty-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #c0c4cc;

    svg {
      stroke: #e4e7ed;
      margin-bottom: 16px;
    }

    p {
      font-size: 14px;
      margin: 0;
    }
  }

  .text-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .text-item {
    background: #f8f9fa;
    border: 2px solid #e4e7ed;
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;

    &.active {
      border-color: #409eff;
      background: #ecf5ff;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
    }

    &.completed {
      border-color: #67c23a;
      background: #f0f9ff;
    }
    
    &.failed {
      border-color: #f56c6c;
      background: #fef0f0;
      opacity: 0.8;
    }

    &.translated {
      background: #f0f9ff;
      border-color: #67c23a;
    }

    .item-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;

      .item-index {
        font-size: 13px;
        font-weight: 600;
        color: #409eff;
        background: #ecf5ff;
        padding: 4px 10px;
        border-radius: 8px;
      }

      .item-type {
        font-size: 12px;
        color: #909399;
        background: #f0f2f5;
        padding: 4px 8px;
        border-radius: 6px;
      }

      .item-page {
        font-size: 12px;
        color: #606266;
        margin-left: auto;
      }

      .item-status {
        display: flex;
        align-items: center;

        &.success svg {
          stroke: #67c23a;
        }
        
        &.failed svg {
          stroke: #f56c6c;
        }

        &.translating .spinner {
          width: 14px;
          height: 14px;
          border: 2px solid #409eff;
          border-top-color: transparent;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      }
    }

    .item-text {
      font-size: 14px;
      line-height: 1.6;
      color: #606266;
      word-break: break-word;
    }
  }
}

.translation-panel .text-item {
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border-color: #91d5ff;
}
</style>
