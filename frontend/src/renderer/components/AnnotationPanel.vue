<template>
  <div
    class="annotation-panel"
    :class="{ 'is-dragging': isDragging, 'is-collapsed': isCollapsed }"
    :style="panelStyle"
    @mousedown="startDrag"
  >
    <div class="panel-header">
      <div class="header-left">
        <div class="header-icon">🐳</div>
        <div class="header-text">
          <span class="panel-title">标注面板</span>
          <span class="panel-hint">选择类型标记元素～</span>
        </div>
      </div>
      <div class="header-right">
        <button class="collapse-btn" @click.stop="toggleCollapse" :title="isCollapsed ? '展开面板' : '收起面板'">
          <svg
            class="collapse-icon"
            :class="{ 'is-rotated': isCollapsed }"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path d="M18 15l-6-6-6 6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
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
      <span class="header-star s1" aria-hidden="true">✦</span>
      <span class="header-star s2" aria-hidden="true">✧</span>
    </div>

    <div class="panel-content" v-show="!isCollapsed" @mousedown.stop>
      <div class="content-section">
        <div class="section-label">
          <span class="section-emoji">🎨</span>
          <span>标注类型</span>
        </div>

        <div v-if="annotationTypes.length === 0" class="empty-state">
          <span class="empty-emoji">🐚</span>
          <span>没有标注类型数据</span>
        </div>
        <div class="type-grid" v-else>
          <div
            v-for="type in annotationTypes"
            :key="type.code"
            class="type-button"
            :style="{ '--type-color': type.color }"
            @click="selectType(type.code)"
          >
            <div class="type-color-bar"></div>
            <div class="type-info">
              <span class="type-dot"></span>
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
// ===== 卡通海洋风配色（与翻译配置弹窗统一） =====
$ink: #3d5a73;
$sub-ink: #8aa2b8;
$blue: #58b6f0;
$blue-dark: #2e8bc7;
$green: #6fce93;
$green-dark: #3fae70;
$coral: #f58b8b;
$coral-dark: #d95f5f;

.annotation-panel {
  position: fixed;
  width: min(340px, 25vw);
  max-width: 340px;
  min-width: 280px;
  background:
    radial-gradient(circle at 15% 20%, #eaf7ff 0 2px, transparent 2px),
    radial-gradient(circle at 80% 60%, #eaf7ff 0 2px, transparent 2px),
    linear-gradient(180deg, #fdfeff 0%, #f4fbff 100%);
  background-size: 80px 80px, 110px 110px, 100% 100%;
  border-radius: 22px;
  border: 3px solid #cfe9fb;
  box-shadow: 0 8px 0 rgba(88, 182, 240, 0.16), 0 18px 40px rgba(46, 90, 122, 0.2);
  z-index: 1000;
  transition: box-shadow 0.25s ease, transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  animation: panel-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);

  &.is-dragging {
    box-shadow: 0 12px 0 rgba(88, 182, 240, 0.18), 0 26px 52px rgba(46, 90, 122, 0.28);
    cursor: move;
    transform: scale(1.02) rotate(-0.5deg);
  }
}

@keyframes panel-pop {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.panel-header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: linear-gradient(135deg, #6fc7f5 0%, #4aa9ec 100%);
  cursor: move;
  user-select: none;
  overflow: hidden;

  // 卡通波浪底边
  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 10px;
    background:
      radial-gradient(circle at 7px -3px, transparent 0 9px, #fdfeff 9px) 0 0 / 22px 10px repeat-x;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    position: relative;
    z-index: 1;
  }

  .header-icon {
    width: 36px;
    height: 36px;
    background: rgba(255, 255, 255, 0.95);
    border: 2px solid #ffffff;
    border-radius: 50%;
    box-shadow: 0 3px 0 rgba(46, 139, 199, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    animation: mascot-bounce 2.8s ease-in-out infinite;
  }

  .header-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .panel-title {
    color: #ffffff;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 1.5px;
    text-shadow: 0 1px 0 rgba(46, 139, 199, 0.45);
  }

  .panel-hint {
    color: rgba(255, 255, 255, 0.85);
    font-size: 11px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
    position: relative;
    z-index: 1;
  }

  .collapse-btn {
    width: 28px;
    height: 28px;
    background: rgba(255, 255, 255, 0.25);
    border: 2px solid rgba(255, 255, 255, 0.6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

    &:hover {
      background: #ffffff;
      color: #4aa9ec;
      transform: scale(1.1);
    }

    &:active {
      transform: scale(0.9);
    }

    .collapse-icon {
      transition: transform 0.3s ease;

      &.is-rotated {
        transform: rotate(180deg);
      }
    }
  }

  .drag-indicator {
    color: rgba(255, 255, 255, 0.5);
    transition: color 0.2s;
    padding: 4px;

    &:hover {
      color: rgba(255, 255, 255, 0.9);
    }
  }

  .header-star {
    position: absolute;
    color: rgba(255, 255, 255, 0.85);
    pointer-events: none;
    animation: twinkle 2.2s ease-in-out infinite;

    &.s1 {
      right: 86px;
      top: 8px;
      font-size: 11px;
    }

    &.s2 {
      right: 130px;
      bottom: 12px;
      font-size: 9px;
      animation-delay: 0.8s;
    }
  }
}

@keyframes mascot-bounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  30% { transform: translateY(-4px) rotate(-6deg); }
  60% { transform: translateY(1px) rotate(4deg); }
}

@keyframes twinkle {
  0%, 100% { opacity: 0.35; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.2); }
}

.panel-content {
  padding: 12px 14px;
  max-height: min(800px, 80vh);
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
    border: 2px solid #f7fbff;

    &:hover {
      background: #9cd3f5;
    }
  }
}

.content-section {
  .section-label {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
    padding: 0 2px;
    color: $ink;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;

    .section-emoji {
      font-size: 14px;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 28px 16px;
  color: $sub-ink;
  font-size: 13px;

  .empty-emoji {
    font-size: 32px;
    opacity: 0.8;
  }
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.type-button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  background: #ffffff;
  border: 2px solid #e3eef8;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;

  &:hover {
    background: color-mix(in srgb, var(--type-color) 8%, #ffffff);
    border-color: var(--type-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 0 color-mix(in srgb, var(--type-color) 30%, #ffffff);

    .type-check {
      opacity: 1;
      transform: scale(1);
    }
  }

  &:active {
    transform: translateY(1px);
    box-shadow: none;
  }

  .type-color-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--type-color);
    border-radius: 0 4px 4px 0;
  }

  .type-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;

    .type-dot {
      width: 11px;
      height: 11px;
      background: var(--type-color);
      border: 2px solid #ffffff;
      box-shadow: 0 0 0 1.5px var(--type-color);
      border-radius: 50%;
      flex-shrink: 0;
    }
  }

  .type-name {
    font-size: 12.5px;
    color: $ink;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .type-check {
    width: 20px;
    height: 20px;
    background: var(--type-color);
    border: 2px solid #ffffff;
    box-shadow: 0 2px 0 color-mix(in srgb, var(--type-color) 60%, #3d5a73);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    opacity: 0;
    transform: scale(0.5);
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    flex-shrink: 0;
  }
}

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 2px dashed #dcecf8;

  .footer-stats {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: $ink;
    font-weight: 700;
  }

  .stat-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    border: 1.5px solid #ffffff;

    &.selected {
      background: $blue;
      box-shadow: 0 0 0 1.5px $blue;
      animation: dot-blink 1.6s ease-in-out infinite;
    }

    &.pending {
      background: $green;
      box-shadow: 0 0 0 1.5px $green;
      animation: dot-blink 1.6s ease-in-out infinite 0.4s;
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
    gap: 5px;
    padding: 8px 12px;
    background: #ffffff;
    color: $sub-ink;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 3px 0 #e2e8f0;

    .cancel-icon {
      transition: transform 0.5s ease;
    }

    &:hover:not(:disabled) {
      color: $ink;
      border-color: #c9d4e0;
      transform: translateY(-2px);
      box-shadow: 0 5px 0 #e2e8f0;

      .cancel-icon {
        animation: rotate-twice 1.5s ease-in-out;
      }
    }

    &:active:not(:disabled) {
      transform: translateY(1px);
      box-shadow: 0 1px 0 #e2e8f0;
    }

    &:disabled {
      background: #f3f5f8;
      border-color: #e9edf2;
      color: #b6bfca;
      box-shadow: none;
      cursor: not-allowed;

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
    gap: 5px;
    padding: 8px 12px;
    background: linear-gradient(135deg, #f99b9b 0%, #f07474 100%);
    color: white;
    border: 2px solid #ffffff;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 3px 0 $coral-dark;

    .trash-lid {
      transform-origin: 22px 5.5px;
      transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 5px 0 $coral-dark;

      .trash-lid {
        transform: rotate(50deg);
      }
    }

    &:active:not(:disabled) {
      transform: translateY(1px);
      box-shadow: 0 1px 0 $coral-dark;
    }

    &:disabled {
      background: #f3f5f8;
      border-color: #e9edf2;
      color: #b6bfca;
      box-shadow: none;
      cursor: not-allowed;

      .trash-lid {
        transform: rotateX(0deg);
      }
    }
  }
}

@keyframes dot-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
</style>
