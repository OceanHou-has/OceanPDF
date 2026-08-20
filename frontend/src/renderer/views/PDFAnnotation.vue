<template>
  <div class="pdf-annotation-page">
    <!-- 顶部工具栏 -->
    <header class="toolbar">
      <div class="left-section">
        <Button1 size="small" @click="goBack" aria-label="返回" title="返回">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </Button1>
        <span class="pdf-name">{{ pdfName }}</span>
      </div>
      <div class="center-section">
        <Button1
          size="small"
          :disabled="currentPage === 0"
          @click="prevPage"
          aria-label="上一页"
          title="上一页"
        >
          <el-icon><ArrowLeftBold /></el-icon>
          <span>上一页</span>
        </Button1>
        <Button1 size="small" disabled aria-label="页码">
          <span>{{ currentPage + 1 }} / {{ totalPages }}</span>
        </Button1>
        <Button1
          size="small"
          :disabled="currentPage >= totalPages - 1"
          @click="nextPage"
          aria-label="下一页"
          title="下一页"
        >
          <el-icon><ArrowRightBold /></el-icon>
          <span>下一页</span>
        </Button1>
      </div>
      <div class="right-section">
        <!-- 论文详细信息按钮 -->
        <Button1 size="small" @click="showPaperInfoDialog = true" aria-label="详细信息" title="详细信息">
          <el-icon><InfoFilled /></el-icon>
          <span>详细信息</span>
        </Button1>
        
        <ToggleSwitch
          v-model="showDpsResults"
          id="pdf-annotation-parse-toggle"
          aria-label="切换解析结果"
          left-label="Python解析"
          right-label="DPS"
          :style="{
            '--_label-padding': '6px 14px',
            '--_switch-padding': '3px'
          }"
          @change="handleResultToggle"
        />

        <!-- 外部解析服务来源徽章（仅当版面结果来自外部服务时显示） -->
        <span
          v-if="layoutSourceBadge"
          class="layout-source-badge"
          :title="`版面分析来源: ${layoutSourceBadge}`"
        >{{ layoutSourceBadge }}</span>

        <!-- 排序模式下的手动排序按钮 -->
        <Button1
          size="small"
          v-if="currentStage === 2"
          @click="toggleManualSorting"
          aria-label="手动排序"
          :title="isManualSorting ? '保存排序' : '手动排序'"
        >
          {{ isManualSorting ? '保存排序' : '手动排序' }}
        </Button1>
        
        <!-- 标注模式下的保存按钮 -->
        <Button1
          size="small"
          v-if="currentStage === 1 && pendingAnnotations.length > 0"
          @click="saveAllAnnotations"
          aria-label="保存标注"
          title="保存标注"
        >
          保存标注 ({{ pendingAnnotations.length }})
        </Button1>
        
        <Button1 size="icon" @click="zoomOut" aria-label="缩小" title="缩小">
          <el-icon><ZoomOut /></el-icon>
        </Button1>
        <span class="zoom-text">{{ Math.round(scale * 100) }}%</span>
        <Button1 size="icon" @click="zoomIn" aria-label="放大" title="放大">
          <el-icon><ZoomIn /></el-icon>
        </Button1>
      </div>
    </header>

    <!-- PDF 显示区域 -->
    <main class="pdf-viewer" @wheel="handleWheel">
      <div class="canvas-container" v-loading="loading" element-loading-text="加载中...">
        <div 
          class="pdf-canvas-wrapper" 
          :style="{ transform: `scale(${scale})`, transformOrigin: 'top center' }"
        >
          <!-- PDF 图片 -->
          <img 
            v-if="pageImage" 
            :src="pageImage" 
            :width="imageWidth"
            :height="imageHeight"
            class="pdf-image"
            ref="pdfImageRef"
          />
          
          <!-- 透明遮罩层 -->
          <div 
            class="transparent-mask"
            :style="{
              width: `${imageWidth}px`,
              height: `${imageHeight}px`
            }"
            @mousedown="handleMaskMouseDown"
          ></div>
          
          <!-- 框选区域 -->
          <div 
            v-if="isSelecting" 
            class="selection-box"
            :style="selectionBoxStyle"
          ></div>
          
          <!-- 标注虚线框（标注模式） -->
          <div
            v-if="currentStage === 1"
            v-for="(element, index) in currentPageElements"
            :key="element.block_id"
            class="annotation-box"
            :class="{ 
              'has-type': element.type,
              'selected': isElementSelected(element)
            }"
            :style="getBoxStyle(element.bbox, element.type)"
            @mouseenter="hoveredElement = index"
            @mouseleave="hoveredElement = null"
            @click="handleBoxClick(element, index)"
          >
            <!-- 右上角标签 -->
            <div v-if="element.type" class="type-label" :style="{ background: getTypeColor(element.type) }">
              {{ getElementTypeDisplayLabel(element) }}
            </div>
            <div v-if="hoveredElement === index" class="annotation-tooltip">
              {{ element.text }}
            </div>
          </div>
          
          <!-- 排序元素框（排序模式） -->
          <div
            v-if="currentStage === 2"
            v-for="(element, index) in sortableElements"
            :key="element.block_id"
            class="sort-box"
            :class="{ 
              'selected': isElementSelected(element),
              'manual-sorting': isManualSorting
            }"
            :style="getBoxStyle(element.bbox, element.type)"
            @click="handleSortBoxClick(element, index)"
          >
            <!-- 中心圆形序号 -->
            <div class="sort-number-badge">
              <span class="sort-number">{{ getElementReadingOrder(element) }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 浮动标注面板（仅标注模式显示） -->
    <AnnotationPanel
      v-if="currentStage === 1"
      :selected-element="selectedLine"
      :selected-count="selectedLines.length"
      :annotation-types="annotationTypeList"
      :pending-count="pendingAnnotations.length"
      @select-type="selectType"
      @clear-annotation="clearCurrentAnnotation"
      @cancel-selection="cancelSelection"
    />
    
    <!-- 合并标注对话框 -->
    <MergeAnnotationDialog
      v-model="showMergeDialog"
      :selected-count="selectedLines.length"
      @merge="handleMergeConfirm"
      @separate="handleSeparateConfirm"
    />
    
    <!-- 退出排序确认对话框 -->
    <SaveSortingDialog
      v-model="showExitSortingDialog"
      @cancel="handleExitSortingCancel"
      @discard="handleExitSortingDiscard"
      @save="handleExitSortingSave"
    />
    
    <!-- 阶段指示器 -->
    <StageIndicator
      v-model="currentStage"
      :completed-stages="completedStages"
      @stage-change="handleStageChange"
    />
    
    <!-- 翻译配置对话框 -->
    <TranslationConfigDialog
      v-model="showTranslationConfigDialog"
      :pdf-name="pdfName"
      @dialog-closed="handleTranslationDialogClosed"
    />
    
    <!-- 论文详细信息对话框 -->
    <PaperInfoDialog
      v-model="showPaperInfoDialog"
      :pdf-name="pdfName"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowLeftBold, ArrowRightBold, ZoomIn, ZoomOut, InfoFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { getAnnotationTypes, annotateElement, clearAnnotation, batchAnnotate, getPDFDpsData } from '../api/pdf'
import AnnotationPanel from '../components/AnnotationPanel.vue'
import MergeAnnotationDialog from '../components/dialogs/MergeAnnotationDialog.vue'
import StageIndicator from '../components/dialogs/StageIndicator.vue'
import SaveSortingDialog from '../components/dialogs/SaveSortingDialog.vue'
import TranslationConfigDialog from '../components/dialogs/TranslationConfigDialog.vue'
import PaperInfoDialog from '../components/dialogs/PaperInfoDialog.vue'
import ToggleSwitch from '../elements/toggle_switch/switch_1.vue'
import Button1 from '../elements/button/button1.vue'

const route = useRoute()
const router = useRouter()

// 基础数据
const pdfName = ref(route.query.pdfName || '')
const currentPage = ref(0)
const totalPages = ref(0)
const scale = ref(1.0)
const loading = ref(false)
const hoveredElement = ref(null)
const showDpsResults = ref(false)

// 框选相关
const isSelecting = ref(false)
const selectionStart = ref({ x: 0, y: 0 })
const selectionEnd = ref({ x: 0, y: 0 })
const selectedLines = ref([]) // 批量选中的元素（变量名保持兼容）

// 标注相关
const annotationTypes = ref([])
const typeColors = ref({})
const selectedLine = ref(null) // 当前选中的元素（变量名保持兼容）
const selectedLineIndex = ref(null) // 兼容变量名
const pendingAnnotations = ref([]) // 暂存待保存的标注
const showMergeDialog = ref(false) // 显示合并对话框
const pendingAnnotationType = ref(null) // 待处理的标注类型

// 阶段管理
const currentStage = ref(1) // 当前阶段: 1=标注, 2=排序, 3=翻译
const completedStages = ref([1]) // 已完成的阶段列表（默认阶段1完成，可随时进入排序）

// 翻译配置对话框
const showTranslationConfigDialog = ref(false)

// 论文详细信息对话框
const showPaperInfoDialog = ref(false)

// 手动排序相关
const isManualSorting = ref(false) // 是否处于手动排序模式
const manualSortingOrder = ref({}) // 存储手动排序的顺序 {block_id: order}
const nextSortOrder = ref(1) // 下一个要分配的排序号
const showExitSortingDialog = ref(false) // 是否显示退出排序确认对话框
const pendingAction = ref(null) // 待执行的操作

// 获取类型标签
const getTypeLabel = (type) => {
  const labels = {
    'document_title': '文档标题',
    'section_title': '章节标题',
    'section_title_2': '二级标题',
    'section_title_3': '三级标题',
    'paragraph': '段落',
    'list': '列表',
    'display_formula': '公式',
    'formula_caption': '公式标题',
    'figure': '图片',
    'figure_caption': '图片标题',
    'table': '表格',
    'table_caption': '表格标题',
    'table_footnote': '表格注释',
    'abandon': '废弃'
  }
  return labels[type] || type
}

const getElementTypeDisplayLabel = (element) => {
  const mappedType = element?.type
  const mappedCn = getTypeLabel(mappedType)
  if (!showDpsResults.value) return mappedCn

  const raw = typeof element?.dps_label === 'string' ? element.dps_label.trim() : ''
  if (!raw) return mappedCn
  return `${raw}${mappedCn}`
}

// 为面板组件准备的数据结构
const annotationTypeList = computed(() => {
  return annotationTypes.value.map(type => ({
    code: type,
    label: getTypeLabel(type),
    color: getTypeColor(type)
  }))
})

// 页面数据
const pageImage = ref('')
const imageWidth = ref(0)
const imageHeight = ref(0)
const parsedData = ref(null)
const dpsData = ref(null)
const pdfImageRef = ref(null)

const dpsLabelToAnnotationType = {
  doc_title: 'document_title',
  title: 'section_title',
  paragraph_title: 'section_title',
  text: 'paragraph',
  abstract: 'paragraph',
  table_of_contents: 'list',
  vision_footnote:'formula_caption',
  reference: 'abandon',
  formula: 'display_formula',
  formula_number: 'formula_caption',
  display_formula: 'display_formula',
  image: 'figure',
  chart:'figure',
  figure: 'figure',
  figure_caption: 'figure_caption',
  figure_title: 'figure_caption',
  table: 'table',
  table_caption: 'table_caption',
  table_title: 'table_caption',
  table_footnote: 'table_footnote',
  list: 'list',
  aside_text: 'paragraph',
  page_number: 'abandon',
  footnote: 'abandon',
  header: 'abandon',
  footer: 'abandon',
  algorithm: 'abandon',
  seal: 'abandon',
  header_image: 'abandon',
  footer_image: 'abandon'
}

const mapDpsLabelToType = (label) => {
  const key = typeof label === 'string' ? label.trim().toLowerCase() : ''
  return dpsLabelToAnnotationType[key] || 'abandon'
}

// 当前页面的元素数据（过滤掉已被合并的源元素）
const pythonCurrentPageElements = computed(() => {
  if (!parsedData.value || !parsedData.value.pages) return []
  const page = parsedData.value.pages[currentPage.value]
  if (!page) return []
  
  // 过滤掉已被合并的源元素
  // 规则：is_merged=true 且 parent_id 不为空的元素不显示
  return page.elements.filter(element => {
    // 如果元素有 parent_id，说明它是被合并的源元素，不显示
    if (element.parent_id) {
      return false
    }
    // 其他情况都显示（包括普通元素和合并元素）
    return true
  })
})

const dpsCurrentPageElements = computed(() => {
  const pages = dpsData.value?.pages ?? dpsData.value?.raw?.pages
  if (!Array.isArray(pages)) return []
  const pageObj = pages.find(p => p?.page_index === currentPage.value) || pages[currentPage.value]
  const boxes = pageObj?.boxes
  if (!Array.isArray(boxes)) return []

  return boxes
    .map((box, idx) => {
      const bbox = box?.coordinate
      const rawLabel = box?.label ?? 'dps'
      const dpsBlockId = box?.DPS_block_id ?? (idx + 1)
      const mappedType = box?.type ?? mapDpsLabelToType(rawLabel)
      const score = box?.score
      const ocrText = typeof box?.ocr_text === 'string' ? box.ocr_text.trim() : ''
      const fallbackText = `${rawLabel}${typeof score === 'number' ? ` (${score.toFixed(3)})` : ''}`
      return {
        block_id: `dps_${currentPage.value}_${dpsBlockId}`,
        dps_block_id: dpsBlockId,
        bbox: Array.isArray(bbox) ? bbox : [],
        type: mappedType,
        dps_label: typeof rawLabel === 'string' ? rawLabel : String(rawLabel),
        reading_order: box?.reading_order,
        text: ocrText || fallbackText
      }
    })
    .filter(e => Array.isArray(e.bbox) && e.bbox.length >= 4)
})

const currentPageElements = computed(() => {
  return showDpsResults.value ? dpsCurrentPageElements.value : pythonCurrentPageElements.value
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

// 版面分析来源徽章：外部服务时显示服务名（本地DPS不显示）
const layoutSourceBadge = computed(() => {
  const meta = dpsData.value?.meta
  if (!meta || !meta.provider || meta.provider === 'dps') return ''
  return meta.provider_name || meta.provider
})

// 排序模式下可排序的元素（只显示章节标题、段落、列表，不包括文档标题）
const sortableElements = computed(() => {
  // DPS模式：显示DPS结果中有reading_order的元素
  if (showDpsResults.value) {
    const pages = dpsData.value?.pages ?? dpsData.value?.raw?.pages
    if (!Array.isArray(pages)) return []
    const pageObj = pages.find(p => p?.page_index === currentPage.value) || pages[currentPage.value]
    const boxes = pageObj?.boxes
    if (!Array.isArray(boxes)) return []
    
    // 过滤出有reading_order的元素（DPS标注的可排序类型）
    return boxes
      .map((box, idx) => {
        const bbox = box?.coordinate
        const readingOrder = box?.reading_order
        const rawLabel = box?.label ?? 'dps'
        const dpsBlockId = box?.DPS_block_id ?? (idx + 1)
        const mappedType = box?.type ?? mapDpsLabelToType(rawLabel)
        
        return {
          block_id: `dps_${currentPage.value}_${dpsBlockId}`,
          dps_block_id: dpsBlockId,
          bbox: Array.isArray(bbox) ? bbox : [],
          type: mappedType,
          dps_label: rawLabel,
          reading_order: readingOrder,
          text: box?.ocr_text || `${rawLabel}`
        }
      })
      .filter(e => {
        if (!Array.isArray(e.bbox) || e.bbox.length < 4) return false
        const sortableTypes = ['section_title', 'section_title_2', 'section_title_3', 'paragraph', 'list']
        if (!sortableTypes.includes(e.type)) return false
        if (isManualSorting.value) return true
        return e.reading_order !== null && e.reading_order !== undefined
      })
  }
  
  // Python模式：原有逻辑
  if (!parsedData.value || !parsedData.value.pages) return []
  const page = parsedData.value.pages[currentPage.value]
  if (!page) return []
  
  // 可排序的类型（不包括document_title）
  const sortableTypes = ['section_title', 'section_title_2', 'section_title_3', 'paragraph', 'list']
  
  return page.elements.filter(element => {
    // 过滤掉被合并的源元素
    if (element.parent_id) return false
    
    // 只保留可排序的类型
    return sortableTypes.includes(element.type)
  })
})

// 返回
const goBack = () => {
  if (isManualSorting.value && Object.keys(manualSortingOrder.value).length > 0) {
    // 有未保存的排序，弹窗确认
    showExitSortingDialog.value = true
    pendingAction.value = () => router.push('/')
  } else {
    router.push('/')
  }
}

// 翻页
const prevPage = () => {
  if (currentPage.value > 0) {
    if (isManualSorting.value && Object.keys(manualSortingOrder.value).length > 0) {
      // 有未保存的排序，弹窗确认
      showExitSortingDialog.value = true
      pendingAction.value = () => {
        currentPage.value--
        // 重置排序状态
        isManualSorting.value = false
        manualSortingOrder.value = {}
        nextSortOrder.value = 1
      }
    } else {
      currentPage.value--
    }
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    if (isManualSorting.value && Object.keys(manualSortingOrder.value).length > 0) {
      // 有未保存的排序，弹窗确认
      showExitSortingDialog.value = true
      pendingAction.value = () => {
        currentPage.value++
        // 重置排序状态
        isManualSorting.value = false
        manualSortingOrder.value = {}
        nextSortOrder.value = 1
      }
    } else {
      currentPage.value++
    }
  }
}

// 缩放
const zoomIn = () => {
  if (scale.value < 3.0) {
    scale.value += 0.2
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value -= 0.2
  }
}

const handleWheel = (e) => {
  if (e.ctrlKey) {
    e.preventDefault()
    if (e.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  }
}

// 框选区域样式
const selectionBoxStyle = computed(() => {
  const x = Math.min(selectionStart.value.x, selectionEnd.value.x)
  const y = Math.min(selectionStart.value.y, selectionEnd.value.y)
  const width = Math.abs(selectionEnd.value.x - selectionStart.value.x)
  const height = Math.abs(selectionEnd.value.y - selectionStart.value.y)
  
  // 坐标已经是相对于遮罩层的像素坐标，直接使用即可
  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`
  }
})

// 判断元素是否被选中
const isElementSelected = (element) => {
  if (selectedLines.value.length > 0) {
    return selectedLines.value.some(e => e.block_id === element.block_id)
  }
  return selectedLine.value && selectedLine.value.block_id === element.block_id
}

// 处理遮罩层鼠标按下
const handleMaskMouseDown = (e) => {
  // 只有在标注模式（阶段1）才允许框选
  if (currentStage.value !== 1) {
    return
  }
  
  // 获取鼠标相对于透明遮罩的坐标，并除以scale转换回原始坐标系
  const mask = e.currentTarget
  const rect = mask.getBoundingClientRect()
  // rect的尺寸已经被scale缩放过了，所以坐标需要除以scale还原
  const x = (e.clientX - rect.left) / scale.value
  const y = (e.clientY - rect.top) / scale.value
  
  isSelecting.value = true
  selectionStart.value = { x, y }
  selectionEnd.value = { x, y }
  
  // 清除之前的选择
  selectedLines.value = []
  selectedLine.value = null
  selectedLineIndex.value = null
  
  // 添加全局鼠标移动和松开事件
  document.addEventListener('mousemove', handleMaskMouseMove)
  document.addEventListener('mouseup', handleMaskMouseUp)
  
  e.preventDefault()
}

// 处理鼠标移动
const handleMaskMouseMove = (e) => {
  if (!isSelecting.value) return
  
  const mask = document.querySelector('.transparent-mask')
  if (!mask) return
  
  const rect = mask.getBoundingClientRect()
  // 坐标需要除以scale转换回原始坐标系
  const x = (e.clientX - rect.left) / scale.value
  const y = (e.clientY - rect.top) / scale.value
  
  selectionEnd.value = { x, y }
}

// 处理鼠标松开
const handleMaskMouseUp = (e) => {
  if (!isSelecting.value) return
  
  // 【关键修复】使用和 getBoxStyle 相同的坐标映射逻辑
  // 1. 获取参考尺寸（PDF原始坐标系的尺寸）
  const refSize = showDpsResults.value ? dpsPageSize.value : pythonPageSize.value
  
  if (!refSize || !refSize.width || !refSize.height) {
    window.$toast?.error('无法获取页面尺寸信息')
    isSelecting.value = false
    document.removeEventListener('mousemove', handleMaskMouseMove)
    document.removeEventListener('mouseup', handleMaskMouseUp)
    return
  }
  
  // 2. 计算从图片坐标系到PDF原始坐标系的缩放比例
  // imageWidth 是渲染的图片宽度，refSize.width 是PDF原始宽度
  const scaleX = refSize.width / imageWidth.value
  const scaleY = refSize.height / imageHeight.value
  
  // 3. 将框选坐标（已除以scale，是图片坐标系）转换为PDF原始坐标
  const minX = Math.min(selectionStart.value.x, selectionEnd.value.x) * scaleX
  const minY = Math.min(selectionStart.value.y, selectionEnd.value.y) * scaleY
  const maxX = Math.max(selectionStart.value.x, selectionEnd.value.x) * scaleX
  const maxY = Math.max(selectionStart.value.y, selectionEnd.value.y) * scaleY
  
  console.log('[框选] 坐标转换信息:', {
    refSize: { width: refSize.width, height: refSize.height },
    imageSize: { width: imageWidth.value, height: imageHeight.value },
    scaleRatio: { x: scaleX, y: scaleY },
    selectionInImageCoords: {
      minX: Math.min(selectionStart.value.x, selectionEnd.value.x),
      minY: Math.min(selectionStart.value.y, selectionEnd.value.y),
      maxX: Math.max(selectionStart.value.x, selectionEnd.value.x),
      maxY: Math.max(selectionStart.value.y, selectionEnd.value.y)
    },
    selectionInPdfCoords: { minX, minY, maxX, maxY }
  })
  
  // 4. 查找完全包含在选择区域内的元素
  const selected = []
  currentPageElements.value.forEach((element) => {
    if (!element.bbox || element.bbox.length < 4) return
    
    const [x0, y0, x1, y1] = element.bbox
    
    // 检查元素是否完全被选择区域包含（使用PDF原始坐标系）
    if (x0 >= minX && x1 <= maxX && y0 >= minY && y1 <= maxY) {
      selected.push(element)
      console.log('[框选] 选中元素:', {
        block_id: element.block_id,
        bbox: element.bbox,
        text: element.text?.substring(0, 30)
      })
    }
  })
  
  selectedLines.value = selected
  
  if (selected.length > 0) {
    window.$toast?.success(`已选中 ${selected.length} 个元素`)
  } else {
    window.$toast?.info('未选中任何元素')
  }
  
  isSelecting.value = false
  
  // 移除全局事件监听
  document.removeEventListener('mousemove', handleMaskMouseMove)
  document.removeEventListener('mouseup', handleMaskMouseUp)
}

// 标注功能
const handleBoxClick = (element, index) => {
  // 单击时切换为单选模式
  selectedLines.value = []
  selectedLine.value = element
  selectedLineIndex.value = index
  window.$toast?.info(`已选中: ${element.text.substring(0, 20)}...`)
}

const selectType = async (type) => {
  // 获取需要标注的元素列表
  const linesToAnnotate = selectedLines.value.length > 0 ? selectedLines.value : 
                          selectedLine.value ? [selectedLine.value] : []
  
  if (linesToAnnotate.length === 0) {
    window.$toast?.warning('请先选择元素框')
    return
  }
  
  // 如果是多选模式，弹窗询问是合并还是单独标注
  if (linesToAnnotate.length > 1) {
    if (showDpsResults.value) {
      separateAnnotate(linesToAnnotate, type)
      return
    }
    pendingAnnotationType.value = type
    showMergeDialog.value = true
  } else {
    // 单选模式，直接单独标注
    separateAnnotate(linesToAnnotate, type)
  }
}

// 处理合并确认
const handleMergeConfirm = () => {
  const linesToAnnotate = selectedLines.value.length > 0 ? selectedLines.value : 
                          selectedLine.value ? [selectedLine.value] : []
  mergeAnnotate(linesToAnnotate, pendingAnnotationType.value)
}

// 处理单独标注确认
const handleSeparateConfirm = () => {
  const linesToAnnotate = selectedLines.value.length > 0 ? selectedLines.value : 
                          selectedLine.value ? [selectedLine.value] : []
  separateAnnotate(linesToAnnotate, pendingAnnotationType.value)
}

// 单独标注函数
const separateAnnotate = (linesToAnnotate, type) => {
  const updateDpsBoxType = (line, newType) => {
    const dpsPages = dpsData.value?.raw?.pages ?? dpsData.value?.pages
    if (!Array.isArray(dpsPages)) return
    const pageObj = dpsPages.find(p => p?.page_index === currentPage.value) || dpsPages[currentPage.value]
    const boxes = pageObj?.boxes
    if (!Array.isArray(boxes)) return

    const dpsBlockId = line?.dps_block_id ?? parseInt(String(line?.block_id || '').split('_').pop(), 10)
    if (!dpsBlockId) return

    const box = boxes.find(b => b?.DPS_block_id === dpsBlockId) ?? boxes[dpsBlockId - 1]
    if (!box) return
    box.type = newType
  }

  linesToAnnotate.forEach(line => {
    // 立即在前端更新显示
    line.type = type
    if (showDpsResults.value) {
      updateDpsBoxType(line, type)
    }
    
    // 记录到待保存列表
    const annotationRecord = {
      page_num: currentPage.value,
      block_id: line.block_id,
      element_type: type
    }
    
    // 检查是否已经有该元素的标注记录
    const existingIndex = pendingAnnotations.value.findIndex(
      a => a.page_num === annotationRecord.page_num && a.block_id === annotationRecord.block_id
    )
    
    if (existingIndex >= 0) {
      // 更新现有记录
      pendingAnnotations.value[existingIndex] = annotationRecord
    } else {
      // 添加新记录
      pendingAnnotations.value.push(annotationRecord)
    }
  })
  
  window.$toast?.success(`已标注 ${linesToAnnotate.length} 个元素为: ${getTypeLabel(type)} (待保存)`)
  
  // 清除选中状态
  selectedLine.value = null
  selectedLineIndex.value = null
  selectedLines.value = []
}

// 合并标注函数
const mergeAnnotate = (linesToAnnotate, type) => {
  // 情况2：检查选中的元素中是否包含合并元素，如果有则先拆解
  const finalLinesToMerge = []
  const currentPageData = parsedData.value.pages[currentPage.value]
  
  linesToAnnotate.forEach(line => {
    if (line.is_merged && line.source_ids && line.source_ids.length > 0) {
      // 这是一个合并元素，需要先拆解
      console.log(`检测到合并元素 ${line.block_id}，先拆解...`)
      
      // 拆解合并元素
      unmergeMergedElement(line)
      
      // 将拆解出的源元素添加到最终合并列表中
      line.source_ids.forEach(sourceId => {
        const sourceElement = currentPageData.elements.find(
          el => el.block_id === sourceId
        )
        if (sourceElement) {
          finalLinesToMerge.push(sourceElement)
        }
      })
    } else {
      // 普通元素，直接添加
      finalLinesToMerge.push(line)
    }
  })
  
  // 去重（可能有重复的源元素）
  const uniqueLines = []
  const seenIds = new Set()
  finalLinesToMerge.forEach(line => {
    if (!seenIds.has(line.block_id)) {
      seenIds.add(line.block_id)
      uniqueLines.push(line)
    }
  })
  
  // 【关键修复】按照 block_id 排序源元素
  // block_id 格式通常是 "p{页码}_{索引}" 或纯数字索引
  uniqueLines.sort((a, b) => {
    const idA = String(a.block_id)
    const idB = String(b.block_id)
    
    // 尝试提取数字进行比较
    const numA = parseInt(idA.replace(/\D/g, '')) || 0
    const numB = parseInt(idB.replace(/\D/g, '')) || 0
    
    return numA - numB
  })
  
  console.log(`最终需要合并的元素数量: ${uniqueLines.length}，已按block_id排序`)
  console.log('排序后的block_id:', uniqueLines.map(l => l.block_id))
  
  // 计算最小包围矩形
  const bboxes = uniqueLines.map(line => line.bbox)
  const minX = Math.min(...bboxes.map(b => b[0]))
  const minY = Math.min(...bboxes.map(b => b[1]))
  const maxX = Math.max(...bboxes.map(b => b[2]))
  const maxY = Math.max(...bboxes.map(b => b[3]))
  const mergedBbox = [minX, minY, maxX, maxY]
  
  // 【关键修复】按排序后的顺序合并文本
  const mergedText = uniqueLines.map(line => line.text).join(' ')
  
  // 收集源元素的 block_id（保持排序后的顺序）
  const sourceIds = uniqueLines.map(line => line.block_id)
  
  // 生成临时的合并元素 block_id（使用时间戳+随机数确保唯一性）
  const tempBlockId = `temp_merged_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  // 创建临时合并元素
  const mergedElement = {
    block_id: tempBlockId,
    bbox: mergedBbox,
    text: mergedText,
    type: type,
    is_merged: true,
    source_ids: sourceIds,
    _is_temp: true  // 标记为临时元素，用于区分
  }
  
  // 立即在前端更新：将源元素标记为已合并
  uniqueLines.forEach(line => {
    line.is_merged = true
    line.parent_id = tempBlockId  // 设置临时父ID
  })
  
  // 将合并元素添加到当前页面的元素列表中
  if (currentPageData && currentPageData.elements) {
    currentPageData.elements.push(mergedElement)
  }
  
  // 将合并标注操作添加到待保存列表
  const mergeRecord = {
    page_num: currentPage.value,
    element_type: type,
    is_merge: true,
    source_elements: uniqueLines.map(line => ({
      block_id: line.block_id,
      bbox: line.bbox,
      text: line.text
    })),
    _temp_block_id: tempBlockId  // 记录临时ID，保存时需要清理
  }
  
  pendingAnnotations.value.push(mergeRecord)
  
  window.$toast?.success(`已将 ${uniqueLines.length} 个元素合并标注为: ${getTypeLabel(type)} (待保存)`)
  console.log('合并后的文本:', mergedText)
  
  // 清除选中状态
  selectedLine.value = null
  selectedLineIndex.value = null
  selectedLines.value = []
}

// 取消选中函数（只清除选中状态，不清除标注）
const cancelSelection = () => {
  // 清除选中状态
  selectedLine.value = null
  selectedLineIndex.value = null
  selectedLines.value = []
  
  window.$toast?.info('已取消选中')
}

// 清除标注函数
const clearCurrentAnnotation = () => {
  const clearDpsBoxType = (line) => {
    const dpsPages = dpsData.value?.raw?.pages ?? dpsData.value?.pages
    if (!Array.isArray(dpsPages)) return
    const pageObj = dpsPages.find(p => p?.page_index === currentPage.value) || dpsPages[currentPage.value]
    const boxes = pageObj?.boxes
    if (!Array.isArray(boxes)) return

    const dpsBlockId = line?.dps_block_id ?? parseInt(String(line?.block_id || '').split('_').pop(), 10)
    if (!dpsBlockId) return

    const box = boxes.find(b => b?.DPS_block_id === dpsBlockId) ?? boxes[dpsBlockId - 1]
    if (!box) return
    delete box.type
  }

  // 获取需要清除标注的元素列表
  const linesToClear = selectedLines.value.length > 0 ? selectedLines.value : 
                       selectedLine.value ? [selectedLine.value] : []
  
  if (linesToClear.length === 0) {
    window.$toast?.warning('请先选择元素框')
    return
  }
  
  // 批量清除
  linesToClear.forEach(line => {
    // 检查是否是合并元素
    if (line.is_merged && line.source_ids && line.source_ids.length > 0) {
      // 情况1：这是一个合并元素框，需要拆解
      unmergeMergedElement(line)
    } else {
      // 普通元素，直接清除标注
      line.type = null
      if (showDpsResults.value) {
        clearDpsBoxType(line)
      }
      
      // 记录清除操作到待保存列表
      const annotationRecord = {
        page_num: currentPage.value,
        block_id: line.block_id,
        element_type: null
      }
      
      const existingIndex = pendingAnnotations.value.findIndex(
        a => a.page_num === annotationRecord.page_num && a.block_id === annotationRecord.block_id
      )
      
      if (existingIndex >= 0) {
        pendingAnnotations.value[existingIndex] = annotationRecord
      } else {
        pendingAnnotations.value.push(annotationRecord)
      }
    }
  })
  
  window.$toast?.success(`已清除 ${linesToClear.length} 个元素的标注 (待保存)`)
  
  // 清除选中状态
  selectedLine.value = null
  selectedLineIndex.value = null
  selectedLines.value = []
}

// 拆解合并元素的辅助函数
const unmergeMergedElement = (mergedElement) => {
  const currentPageData = parsedData.value.pages[currentPage.value]
  if (!currentPageData || !currentPageData.elements) return
  
  // 找到所有源元素并还原状态
  currentPageData.elements.forEach(element => {
    if (mergedElement.source_ids.includes(element.block_id)) {
      // 还原源元素状态
      element.is_merged = false
      delete element.parent_id
    }
  })
  
  // 从元素列表中移除这个合并元素
  const mergedIndex = currentPageData.elements.findIndex(
    el => el.block_id === mergedElement.block_id
  )
  if (mergedIndex !== -1) {
    currentPageData.elements.splice(mergedIndex, 1)
  }
  
  // 如果这是临时合并元素，从待保存列表中移除对应的合并记录
  if (mergedElement._is_temp) {
    const pendingIndex = pendingAnnotations.value.findIndex(
      a => a._temp_block_id === mergedElement.block_id
    )
    if (pendingIndex !== -1) {
      pendingAnnotations.value.splice(pendingIndex, 1)
    }
  } else {
    // 如果是已保存的合并元素，需要记录拆解操作到待保存列表
    // 为每个源元素添加清除标注记录
    mergedElement.source_ids.forEach(sourceId => {
      const annotationRecord = {
        page_num: currentPage.value,
        block_id: sourceId,
        element_type: null,
        unmerge_from: mergedElement.block_id  // 标记这是拆解操作（不带下划线）
      }
      pendingAnnotations.value.push(annotationRecord)
    })
  }
}

// 保存所有标注到后端
const saveAllAnnotations = async () => {
  if (pendingAnnotations.value.length === 0) {
    window.$toast?.warning('没有待保存的标注')
    return
  }
  
  try {
    // 清理临时标记，准备发送的数据
    const cleanedAnnotations = pendingAnnotations.value.map(annotation => {
      const { _temp_block_id, ...cleanData } = annotation
      return cleanData
    })
    
    // 使用批量接口一次性提交所有标注
    await batchAnnotate({
      pdf_name: pdfName.value,
      annotations: cleanedAnnotations,
      use_dps: showDpsResults.value
    })
    
    window.$toast?.success(`已保存 ${pendingAnnotations.value.length} 个标注`)
    pendingAnnotations.value = []
    
    // 重新加载数据以确保与后端同步（这会用后端的真实数据替换临时数据）
    if (showDpsResults.value) {
      await loadDpsData()
    } else {
      await loadParsedData()
    }
  } catch (error) {
    console.error('保存失败详情：', error)
    window.$toast?.error('保存失败：' + error.message)
  }
}

const getTypeColor = (type) => {
  if (type === 'display_formula') return '#7C3AED'
  if (type === 'formula_caption') return '#A78BFA'
  return typeColors.value[type] || '#409EFF'
}

// 获取标注框样式
const getBoxStyle = (bbox, type) => {
  if (!bbox || bbox.length < 4) return {}
  
  const [x0, y0, x1, y1] = bbox

  const refSize = showDpsResults.value ? dpsPageSize.value : pythonPageSize.value
  const scaleX = refSize?.width ? imageWidth.value / refSize.width : (showDpsResults.value ? 1.0 : 2.0)
  const scaleY = refSize?.height ? imageHeight.value / refSize.height : (showDpsResults.value ? 1.0 : 2.0)

  const style = {
    left: `${x0 * scaleX}px`,
    top: `${y0 * scaleY}px`,
    width: `${(x1 - x0) * scaleX}px`,
    height: `${(y1 - y0) * scaleY}px`
  }
  
  // 如果有类型，设置边框颜色
  if (type) {
    style.borderColor = getTypeColor(type)
    style.background = getTypeColor(type) + '15' // 添加透明度
  }
  
  return style
}

// 加载PDF页面图片
const loadPageImage = async () => {
  loading.value = true
  try {
    const response = await axios.get(
      `http://127.0.0.1:8000/api/v1/pdf/${pdfName.value}/page/${currentPage.value}`
    )
    
    if (response.data.code === 200) {
      pageImage.value = response.data.data.image
      imageWidth.value = response.data.data.width
      imageHeight.value = response.data.data.height
      console.log('[PDFAnnotation] 页面图片加载完成:', {
        page: currentPage.value,
        imageWidth: imageWidth.value,
        imageHeight: imageHeight.value
      })
    }
  } catch (error) {
    window.$toast?.error('加载PDF页面失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载解析数据
const loadParsedData = async () => {
  try {
    console.log('[PDFAnnotation] 开始加载Python解析数据:', { pdfName: pdfName.value })
    const response = await axios.get(
      `http://127.0.0.1:8000/api/v1/pdf/${pdfName.value}/parsed`
    )
    
    if (response.data.code === 200) {
      parsedData.value = response.data.data
      totalPages.value = parsedData.value.total_pages
      console.log('[PDFAnnotation] Python解析数据加载完成:', {
        pdfName: pdfName.value,
        totalPages: totalPages.value,
        pagesLen: Array.isArray(parsedData.value?.pages) ? parsedData.value.pages.length : null
      })
    }
  } catch (error) {
    window.$toast?.error('加载解析数据失败：' + error.message)
  }
}

const loadDpsData = async () => {
  try {
    console.log('[PDFAnnotation] 开始加载DPS解析数据:', { pdfName: pdfName.value })
    const response = await getPDFDpsData(pdfName.value)
    // 获取 data 字段
    const data = response.data
    dpsData.value = data
    console.log('[PDFAnnotation] DPS解析数据加载完成:', {
      pdfName: pdfName.value,
      pagesLen: Array.isArray(data?.pages) ? data.pages.length : Array.isArray(data?.raw?.pages) ? data.raw.pages.length : null,
      withOcr: data?.meta?.with_ocr ?? data?.with_ocr ?? null,
      reqId: data?.meta?.req_id ?? data?.req_id ?? data?.raw?.req_id ?? null
    })

    const pages = data?.pages ?? data?.raw?.pages
    if (Array.isArray(pages)) {
      const counts = {}
      for (const p of pages) {
        const boxes = p?.boxes
        if (!Array.isArray(boxes)) continue
        for (const b of boxes) {
          const rawLabel = b?.label ?? 'dps'
          const mappedType = mapDpsLabelToType(rawLabel)
          const key = `${rawLabel} -> ${mappedType}`
          counts[key] = (counts[key] || 0) + 1
        }
      }
      console.log('[PDFAnnotation] DPS标签映射统计:', counts)
    }
  } catch (error) {
    console.error('[PDFAnnotation] DPS解析数据加载失败:', error)
    window.$toast?.error('加载DPS解析数据失败：' + error.message)
    throw error
  }
}

const handleResultToggle = async (val) => {
  if (val) {
    if (isManualSorting.value && Object.keys(manualSortingOrder.value).length > 0) {
      window.$toast?.warning('当前有未保存的排序，先保存或退出排序后再切换')
      showDpsResults.value = false
      return
    }
    if (!dpsData.value) {
      try {
        await loadDpsData()
      } catch (e) {
        showDpsResults.value = false
        return
      }
    }
    // DPS模式下允许阶段1和阶段2，如果在阶段3则切回阶段1
    if (currentStage.value === 3) {
      currentStage.value = 1
    }
    showMergeDialog.value = false
    pendingAnnotationType.value = null
    hoveredElement.value = null
    selectedLines.value = []
    selectedLine.value = null
    selectedLineIndex.value = null
    console.log('[PDFAnnotation] 已切换到DPS结果视图')
  } else {
    showMergeDialog.value = false
    pendingAnnotationType.value = null
    hoveredElement.value = null
    selectedLines.value = []
    selectedLine.value = null
    selectedLineIndex.value = null
    console.log('[PDFAnnotation] 已切换到Python结果视图')
  }
}

// 监听页码变化
watch(currentPage, () => {
  loadPageImage()
  if (showDpsResults.value) {
    const ref = dpsPageSize.value
    console.log('[PDFAnnotation] DPS坐标映射信息:', {
      page: currentPage.value,
      dpsPageWidth: ref?.width ?? null,
      dpsPageHeight: ref?.height ?? null,
      imageWidth: imageWidth.value,
      imageHeight: imageHeight.value,
      scaleX: ref?.width ? imageWidth.value / ref.width : null,
      scaleY: ref?.height ? imageHeight.value / ref.height : null
    })
  } else {
    const ref = pythonPageSize.value
    console.log('[PDFAnnotation] Python坐标映射信息:', {
      page: currentPage.value,
      pageWidth: ref?.width ?? null,
      pageHeight: ref?.height ?? null,
      imageWidth: imageWidth.value,
      imageHeight: imageHeight.value,
      scaleX: ref?.width ? imageWidth.value / ref.width : null,
      scaleY: ref?.height ? imageHeight.value / ref.height : null
    })
  }
})

// 初始化
onMounted(async () => {
  if (!pdfName.value) {
    window.$toast?.error('缺少PDF名称参数')
    goBack()
    return
  }
  
  // 加载标注类型
  try {
    const response = await getAnnotationTypes()
    console.log('[PDFAnnotation] 标注类型原始响应:', response)
    // request拦截器返回完整的响应对象，需要从 data 字段获取
    if (response && response.data) {
      annotationTypes.value = response.data.types
      typeColors.value = response.data.colors
      console.log('[PDFAnnotation] 标注类型已加载:', {
        typeCount: annotationTypes.value?.length ?? 0,
        types: annotationTypes.value
      })

      const required = ['section_title', 'section_title_2', 'section_title_3']
      const missing = required.filter(t => !annotationTypes.value.includes(t))
      if (missing.length > 0) {
        window.$toast?.warning(`标注类型缺失: ${missing.join(', ')}`)
        console.warn('[PDFAnnotation] 标注类型缺失，可能后端未更新/未重启:', missing)
      }
    }
  } catch (error) {
    console.error('加载标注类型失败:', error)
  }
  
  await loadParsedData()
  await loadPageImage()
})

// 处理阶段切换
const handleStageChange = (stageId) => {
  // DPS模式下允许切换到阶段1（标注）和阶段2（排序），但不允许阶段3（翻译）
  if (showDpsResults.value && stageId === 3) {
    window.$toast?.info('DPS结果预览模式不支持翻译阶段')
    return
  }
  
  // 如果切换到翻译阶段，直接弹出翻译配置对话框（无需先完成阶段2）
  if (stageId === 3) {
    showTranslationConfigDialog.value = true
    // 不改变 currentStage，等生成预翻译文件后再切换
    return
  }
  
  // 如果在排序模式下切换阶段，检查是否有未保存的排序
  if (isManualSorting.value && Object.keys(manualSortingOrder.value).length > 0) {
    showExitSortingDialog.value = true
    pendingAction.value = () => {
      // 清除选中状态
      selectedLine.value = null
      selectedLineIndex.value = null
      selectedLines.value = []
      
      // 重置排序状态
      isManualSorting.value = false
      manualSortingOrder.value = {}
      nextSortOrder.value = 1
    }
    return
  }
  
  // 切换阶段时清除选中状态
  selectedLine.value = null
  selectedLineIndex.value = null
  selectedLines.value = []
  
  // 切换离开排序阶段时，退出手动排序模式
  if (stageId !== 2 && isManualSorting.value) {
    isManualSorting.value = false
    manualSortingOrder.value = {}
    nextSortOrder.value = 1
  }
}

// 切换手动排序模式
const toggleManualSorting = async () => {
  if (!isManualSorting.value) {
    // 进入手动排序模式
    isManualSorting.value = true
    manualSortingOrder.value = {}
    nextSortOrder.value = 1
    window.$toast?.info('请依次点击元素框设置阅读顺序')
  } else {
    // 保存排序结果
    await saveManualSorting()
  }
}

// 保存手动排序结果
const saveManualSorting = async () => {
  try {
    // 构造批量更新请求
    const annotations = []
    
    // 第一步：处理已手动设置的元素
    const manuallySetElements = []
    const remainingElements = []
    
    for (const element of sortableElements.value) {
      if (manualSortingOrder.value[element.block_id]) {
        // 已手动设置的元素
        manuallySetElements.push({
          element,
          order: manualSortingOrder.value[element.block_id]
        })
      } else {
        // 未设置的元素，留待后续处理
        remainingElements.push(element)
      }
    }
    
    // 按手动设置的顺序排序
    manuallySetElements.sort((a, b) => a.order - b.order)
    
    // 对未设置的元素按block_id排序（合并元素使用第一个source_ids）
    remainingElements.sort((a, b) => {
      if (showDpsResults.value) {
        return Number(a.dps_block_id || 0) - Number(b.dps_block_id || 0)
      }

      const aId = a.is_merged && a.source_ids && a.source_ids.length > 0 
        ? a.source_ids[0] 
        : a.block_id
      const bId = b.is_merged && b.source_ids && b.source_ids.length > 0 
        ? b.source_ids[0] 
        : b.block_id
      
      // 比较，支持字符串和数字类型
      if (typeof aId === 'string' && typeof bId === 'string') {
        return aId.localeCompare(bId)
      }
      return Number(aId) - Number(bId)
    })
    
    // 第二步：合并所有元素，分配连续的阅读顺序
    let currentOrder = 1
    
    // 先添加手动设置的元素
    for (const { element } of manuallySetElements) {
      annotations.push({
        page_num: currentPage.value,
        block_id: element.block_id,
        element_type: element.type,
        reading_order: currentOrder++
      })
    }
    
    // 再添加未设置的元素，顺序接着后面
    for (const element of remainingElements) {
      annotations.push({
        page_num: currentPage.value,
        block_id: element.block_id,
        element_type: element.type,
        reading_order: currentOrder++
      })
    }
    
    if (annotations.length === 0) {
      window.$toast?.warning('没有需要保存的排序')
      return false
    }
    
    // 调用API保存
    const response = await batchAnnotate({
      pdf_name: pdfName.value,
      annotations: annotations,
      use_dps: showDpsResults.value
    })
    
    window.$toast?.success('排序保存成功！')
    
    // 退出手动排序模式
    isManualSorting.value = false
    manualSortingOrder.value = {}
    nextSortOrder.value = 1
    
    // 重新加载数据
    if (showDpsResults.value) {
      await loadDpsData()
    } else {
      await loadParsedData()
    }
    
    return true
    
  } catch (error) {
    console.error('保存排序失败:', error)
    window.$toast?.error('保存排序失败！')
    return false
  }
}

// 获取元素的阅读顺序显示
const getElementReadingOrder = (element) => {
  if (isManualSorting.value) {
    // 手动排序模式：显示已设置的顺序
    return manualSortingOrder.value[element.block_id] || '-'
  } else {
    // 普通模式：显示从后端加载的顺序
    return element.reading_order || '-'
  }
}

// 处理排序框点击
const handleSortBoxClick = (element, index) => {
  if (isManualSorting.value) {
    // 手动排序模式
    const blockId = element.block_id
    
    if (manualSortingOrder.value[blockId]) {
      // 已经有顺序，点击取消
      const canceledOrder = manualSortingOrder.value[blockId]
      delete manualSortingOrder.value[blockId]
      
      // 重新调整所有大于被取消顺序的元素
      for (const key in manualSortingOrder.value) {
        if (manualSortingOrder.value[key] > canceledOrder) {
          manualSortingOrder.value[key]--
        }
      }
      
      nextSortOrder.value--
      window.$toast?.info(`已取消顺序 ${canceledOrder}`)
    } else {
      // 还没有顺序，分配新顺序
      manualSortingOrder.value[blockId] = nextSortOrder.value
      window.$toast?.success(`设置顺序为 ${nextSortOrder.value}`)
      nextSortOrder.value++
    }
    
    // 强制响应式更新
    manualSortingOrder.value = { ...manualSortingOrder.value }
  } else {
    // 普通查看模式
    selectedLines.value = []
    selectedLine.value = element
    selectedLineIndex.value = index
    window.$toast?.info(`阅读顺序: ${element.reading_order || '未设置'}`)
  }
}

// 处理退出排序对话框 - 取消操作
const handleExitSortingCancel = () => {
  showExitSortingDialog.value = false
  pendingAction.value = null
}

// 处理退出排序对话框 - 不保存
const handleExitSortingDiscard = () => {
  showExitSortingDialog.value = false
  
  // 重置排序状态
  isManualSorting.value = false
  manualSortingOrder.value = {}
  nextSortOrder.value = 1
  
  // 执行待执行的操作
  if (pendingAction.value) {
    pendingAction.value()
    pendingAction.value = null
  }
}

// 处理退出排序对话框 - 保存排序
const handleExitSortingSave = async () => {
  showExitSortingDialog.value = false
  
  // 保存排序
  const success = await saveManualSorting()
  
  // 如果保存成功，执行待执行的操作
  if (success && pendingAction.value) {
    pendingAction.value()
    pendingAction.value = null
  }
}

// 处理翻译配置对话框关闭
const handleTranslationDialogClosed = () => {
  // 对话框关闭时不需要做任何操作
  // 当前阶段在打开弹窗时没有改变，所以关闭时也不需要回退
}
</script>

<style scoped lang="scss">
.pdf-annotation-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

// 外部解析服务来源徽章
.layout-source-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 999px;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(79, 172, 254, 0.35);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .left-section {
    display: flex;
    align-items: center;
    gap: 16px;

    .pdf-name {
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  .center-section {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
  }

  .right-section {
    display: flex;
    align-items: center;
    gap: 12px;

    .zoom-text {
      font-size: 14px;
      color: #606266;
      min-width: 50px;
      text-align: center;
    }
  }
}

.pdf-viewer {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 24px;
  
  .canvas-container {
    display: flex;
    justify-content: center;
    min-width: 100%;
  }

  .pdf-canvas-wrapper {
    position: relative;
    background: white;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    transition: transform 0.2s ease;
  }

  .pdf-image {
    display: block;
    user-select: none;
  }
  
  .transparent-mask {
    position: absolute;
    top: 0;
    left: 0;
    cursor: crosshair;
    z-index: 1;
  }
  
  .selection-box {
    position: absolute;
    border: 2px solid #409eff;
    background: rgba(64, 158, 255, 0.15);
    pointer-events: none;
    z-index: 3;
  }

  .annotation-box {
    position: absolute;
    border: 2px dashed #409eff;
    background: rgba(64, 158, 255, 0.05);
    cursor: pointer;
    transition: all 0.2s;
    pointer-events: auto;
    z-index: 2;

    &:hover {
      border-width: 3px;
      box-shadow: 0 0 10px rgba(64, 158, 255, 0.3);
      z-index: 10;
    }
    
    &.has-type {
      border-style: solid;
      border-width: 2px;
    }
    
    &.selected {
      border-width: 3px;
      border-style: solid;
      box-shadow: 0 0 15px rgba(255, 193, 7, 0.6);
      z-index: 100;
      animation: pulse 1.5s infinite;
    }
  }
  
  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 0 15px rgba(255, 193, 7, 0.6);
    }
    50% {
      box-shadow: 0 0 25px rgba(255, 193, 7, 0.8);
    }
  }
  
  .type-label {
    position: absolute;
    top: -2px;
    right: -2px;
    padding: 2px 8px;
    font-size: 12px;
    color: white;
    border-radius: 0 0 0 4px;
    white-space: nowrap;
    font-weight: 500;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .annotation-tooltip {
    position: absolute;
    bottom: 100%;
    left: 0;
    margin-bottom: 8px;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.85);
    color: white;
    font-size: 13px;
    border-radius: 4px;
    white-space: pre-wrap;  /* 改为 pre-wrap 支持换行 */
    word-wrap: break-word;  /* 强制换行 */
    max-width: 600px;  /* 增加最大宽度 */
    min-width: 200px;  /* 设置最小宽度 */
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    line-height: 1.5;  /* 增加行高便于阅读 */
  }
  
  // 排序模式样式
  .sort-box {
    position: absolute;
    border: 3px solid #409eff;
    background: rgba(64, 158, 255, 0.08);
    cursor: pointer;
    transition: all 0.2s;
    pointer-events: auto;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      border-color: #66b1ff;
      background: rgba(64, 158, 255, 0.12);
      box-shadow: 0 0 15px rgba(64, 158, 255, 0.4);
      z-index: 10;
    }
    
    // 手动排序模式
    &.manual-sorting {
      border-color: #10b981;
      background: rgba(16, 185, 129, 0.1);
      
      &:hover {
        border-color: #34d399;
        background: rgba(16, 185, 129, 0.15);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
      }
      
      .sort-number-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        animation: pulse-waiting 2s infinite;
      }
    }
    
    &.selected {
      border-width: 4px;
      border-color: #ffc107;
      background: rgba(255, 193, 7, 0.1);
      box-shadow: 0 0 20px rgba(255, 193, 7, 0.5);
      z-index: 100;
      animation: sortPulse 1.5s infinite;
    }
    
    .sort-number-badge {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 
        0 3px 12px rgba(139, 92, 246, 0.4),
        0 0 0 3px rgba(255, 255, 255, 0.95);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      
      .sort-number {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        user-select: none;
      }
    }
    
    &:hover .sort-number-badge {
      transform: scale(1.1);
      box-shadow: 
        0 4px 15px rgba(139, 92, 246, 0.5),
        0 0 0 4px rgba(255, 255, 255, 1);
    }
    
    &.selected .sort-number-badge {
      background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
      box-shadow: 
        0 5px 20px rgba(245, 158, 11, 0.6),
        0 0 0 4px rgba(255, 255, 255, 1);
      transform: scale(1.15);
    }
  }
  
  @keyframes sortPulse {
    0%, 100% {
      box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
    }
    50% {
      box-shadow: 0 0 30px rgba(245, 158, 11, 0.7);
    }
  }
  
  @keyframes pulse-waiting {
    0%, 100% {
      box-shadow: 
        0 3px 12px rgba(16, 185, 129, 0.4),
        0 0 0 3px rgba(255, 255, 255, 0.95);
    }
    50% {
      box-shadow: 
        0 4px 15px rgba(16, 185, 129, 0.6),
        0 0 0 4px rgba(255, 255, 255, 1);
    }
  }
}
</style>
