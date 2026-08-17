<template>
  <div
    class="annotation-panel"
    :class="{ 'is-dragging': isDragging, 'is-collapsed': isCollapsed }"
    :style="panelStyle"
    @mousedown="startDrag"
  >
    <div class="panel-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M7 3H5C3.89543 3 3 3.89543 3 5V7M7 21H5C3.89543 21 3 20.1046 3 19V17M21 5V7C21 8.10457 20.1046 9 19 9H17M21 19V17C21 15.8954 20.1046 15 19 15H17M17 21H19C20.1046 21 21 20.1046 21 19M7 17H17M7 7H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="header-text">
          <span class="panel-title">标注面板</span>
          <span class="panel-hint">选择类型标记元素</span>
        </div>
      </div>
      <div class="header-right">
        <button class="collapse-btn" @click.stop="toggleCollapse">
          <svg 
            class="collapse-icon" 
            :class="{ 'is-rotated': isCollapsed }"
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none"
          >
            <path d="M18 15l-6-6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <div class="drag-indicator">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="9" cy="5" r="1.5" fill="currentColor"/>
            <circle cx="15" cy="5" r="1.5" fill="currentColor"/>
            <circle cx="9" cy="12" r="1.5" fill="currentColor"/>
            <circle cx="15" cy="12" r="1.5" fill="currentColor"/>
            <circle cx="9" cy="19" r="1.5" fill="currentColor"/>
            <circle cx="15" cy="19" r="1.5" fill="currentColor"/>
          </svg>
        </div>
      </div>
    </div>

    <div class="panel-content" v-show="!isCollapsed" @mousedown.stop>
      <div class="content-section">
        <div class="section-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>标注类型</span>
        </div>

        <div v-if="annotationTypes.length === 0" class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
            <path d="M12 8v4m0 4h.01M5.07 19H19a2 2 0 001.75-2.97L13.75 4a2 2 0 00-3.5 0L3.32 16.03A2 2 0 005.07 19z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>没有标注类型数据</span>
        </div>
        <div class="type-grid" v-else>
          <div
            v-for="type in annotationTypes"
            :key="type.code"
            class="type-button"
            :style="{ 
              '--type-color': type.color
            }"
            @click="selectType(type.code)"
          >
            <div class="type-color-bar"></div>
            <div class="type-info">
              <span class="type-name">{{ type.label }}</span>
            </div>
            <div class="type-check">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-footer">
        <div class="footer-stats">
          <div class="stat-item" v-if="selectedElement || selectedCount > 0">
            <div class="stat-dot selected"></div>
            <span>已选 {{ selectedCount }}</span>
          </div>
          <div class="stat-item" v-if="pendingCount > 0">
            <div class="stat-dot pending"></div>
            <span>待保存 {{ pendingCount }}</span>
          </div>
        </div>
        <div class="footer-actions">
          <button 
            class="cancel-btn"
            :disabled="!selectedElement && selectedCount === 0"
            @click="cancelSelection"
          >
            <svg class="cancel-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            取消标注
          </button>
          <button 
            class="clear-btn"
            :disabled="!selectedElement && selectedCount === 0"
            @click="clearAnnotation"
          >
            <svg class="trash-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
              <g class="trash-lid">
                <rect x="2" y="4" width="20" height="3" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
                <path d="M9 4V3a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
              </g>
              <rect x="3" y="7" width="18" height="13" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
              <line x1="8" y1="10" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="12" y1="10" x2="12" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="16" y1="10" x2="16" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            清除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  selectedElement: {
    type: Object,
    default: null
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  annotationTypes: {
    type: Array,
    default: () => []
  },
  pendingCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select-type', 'clear-annotation', 'cancel-selection'])

const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 拖拽相关
const isDragging = ref(false)
const panelPosition = ref({ x: 20, y: 150 })
const dragStart = ref({ x: 0, y: 0 })

// 确保面板在视口范围内
const constrainPosition = () => {
  const maxX = window.innerWidth - 260
  const maxY = window.innerHeight - 100
  
  panelPosition.value.x = Math.max(0, Math.min(panelPosition.value.x, maxX))
  panelPosition.value.y = Math.max(0, Math.min(panelPosition.value.y, maxY))
}

const panelStyle = computed(() => ({
  left: `${panelPosition.value.x}px`,
  top: `${panelPosition.value.y}px`
}))

const startDrag = (e) => {
  // 只在标题栏区域可以拖动
  if (!e.target.closest('.panel-header')) return
  
  isDragging.value = true
  dragStart.value = {
    x: e.clientX - panelPosition.value.x,
    y: e.clientY - panelPosition.value.y
  }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  let newX = e.clientX - dragStart.value.x
  let newY = e.clientY - dragStart.value.y
  
  // 限制在窗口范围内
  const maxX = window.innerWidth - 260
  const maxY = window.innerHeight - 100
  
  newX = Math.max(0, Math.min(newX, maxX))
  newY = Math.max(0, Math.min(newY, maxY))
  
  panelPosition.value = { x: newX, y: newY }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const selectType = (typeCode) => {
  if (!props.selectedElement && props.selectedCount === 0) {
    window.$toast?.warning('请先点击选择一个元素框')
    return
  }
  
  emit('select-type', typeCode)
}

const clearAnnotation = () => {
  if (!props.selectedElement && props.selectedCount === 0) {
    window.$toast?.warning('请先选择一个元素框')
    return
  }
  
  emit('clear-annotation')
}

const cancelSelection = () => {
  if (!props.selectedElement && props.selectedCount === 0) {
    window.$toast?.warning('请先选择一个元素框')
    return
  }
  
  emit('cancel-selection')
}

// 监听窗口大小变化
const handleResize = () => {
  constrainPosition()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 初始化时也确保位置正确
  constrainPosition()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.annotation-panel {
  position: fixed;
  width: min(340px, 25vw);
  max-width: 340px;
  min-width: 280px;
  background: linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 16px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  z-index: 1000;
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  overflow: hidden;
  
  &.is-dragging {
    box-shadow: 
      0 16px 48px rgba(0, 0, 0, 0.2),
      0 4px 16px rgba(0, 0, 0, 0.12);
    cursor: move;
    transform: scale(1.02);
  }
  
  &.is-collapsed {
    .panel-header {
      border-radius: 16px;
    }
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(135deg, #1e88e5 0%, #42a5f5 100%);
  cursor: move;
  user-select: none;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .header-icon {
    width: 34px;
    height: 34px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }
  
  .header-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .panel-title {
    color: white;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.5px;
  }
  
  .panel-hint {
    color: rgba(255, 255, 255, 0.6);
    font-size: 11px;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .collapse-btn {
    width: 28px;
    height: 28px;
    background: rgba(102, 187, 106, 0.9);
    border: none;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(102, 187, 106, 1);
      transform: scale(1.05);
    }
    
    .collapse-icon {
      transition: transform 0.3s ease;
      
      &.is-rotated {
        transform: rotate(180deg);
      }
    }
  }
  
  .drag-indicator {
    color: rgba(255, 255, 255, 0.4);
    transition: color 0.2s;
    padding: 4px;
    
    &:hover {
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

.panel-content {
  padding: 14px 16px;
  max-height: min(800px, 80vh);
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    
    &:hover {
      background: rgba(0, 0, 0, 0.25);
    }
  }
}

.content-section {
  .section-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 0 4px;
    color: #606266;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    
    svg {
      opacity: 0.6;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px 16px;
  color: #909399;
  font-size: 13px;
  
  svg {
    opacity: 0.4;
  }
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.type-button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  
  &:hover {
    background: #ecf5ff;
    transform: translateX(4px);
    
    .type-color-bar {
      width: 4px;
    }
    
    .type-check {
      opacity: 1;
      transform: scale(1);
    }
  }
  
  &:active {
    transform: translateX(4px) scale(0.98);
  }
  
  .type-color-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--type-color);
    border-radius: 10px 0 0 10px;
    transition: width 0.25s ease;
  }
  
  .type-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 10px;
    
    &::before {
      content: '';
      width: 10px;
      height: 10px;
      background: var(--type-color);
      border-radius: 3px;
      flex-shrink: 0;
    }
  }
  
  .type-name {
    font-size: 13px;
    color: #303133;
    font-weight: 500;
  }
  
  .type-check {
    width: 22px;
    height: 22px;
    background: var(--type-color);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    opacity: 0;
    transform: scale(0.5);
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(30, 136, 229, 0.08);
  
  .footer-stats {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #606266;
  }
  
  .stat-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    
    &.selected {
      background: #409eff;
      box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
    }
    
    &.pending {
      background: #67c23a;
      box-shadow: 0 0 8px rgba(103, 194, 58, 0.5);
    }
  }
  
  .footer-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .cancel-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    background: linear-gradient(135deg, #909399 0%, #606266 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(144, 147, 153, 0.3);
    
    .cancel-icon {
      transition: transform 0.5s ease;
    }
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(144, 147, 153, 0.4);
      
      .cancel-icon {
        animation: rotate-twice 1.5s ease-in-out;
      }
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
    
    &:disabled {
      background: linear-gradient(135deg, #c0c4cc 0%, #a8abb2 100%);
      box-shadow: none;
      cursor: not-allowed;
      opacity: 0.7;
      
      .cancel-icon {
        animation: none;
      }
    }
  }
  
  @keyframes rotate-twice {
    0% {
      transform: rotate(0deg);
    }
    45% {
      transform: rotate(360deg);
    }
    55% {
      transform: rotate(360deg);
    }
    100% {
      transform: rotate(720deg);
    }
  }
  
  .clear-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 9px 14px;
    background: linear-gradient(135deg, #f56c6c 0%, #e64a4a 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(245, 108, 108, 0.3);
    
    .trash-lid {
      transform-origin: 22px 5.5px;
      transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
      
      .trash-lid {
        transform: rotate(50deg);
      }
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
    
    &:disabled {
      background: linear-gradient(135deg, #c0c4cc 0%, #a8abb2 100%);
      box-shadow: none;
      cursor: not-allowed;
      opacity: 0.7;
      
      .trash-lid {
        transform: rotateX(0deg);
      }
    }
  }
}
</style>
