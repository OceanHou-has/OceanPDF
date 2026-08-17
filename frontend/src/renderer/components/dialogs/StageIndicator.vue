<template>
  <div class="stage-indicator">
    <div class="stage-container">
      <div
        v-for="stage in stages"
        :key="stage.id"
        class="stage-item"
        :class="{
          'is-active': currentStage === stage.id,
          'is-completed': isStageCompleted(stage.id),
          'is-disabled': isStageDisabled(stage.id)
        }"
        @click="handleStageClick(stage.id)"
      >
        <div class="stage-badge">
          <div class="progress-ring">
            <svg width="56" height="56" viewBox="0 0 56 56">
              <circle
                cx="28"
                cy="28"
                r="26"
                class="progress-ring-circle"
              />
            </svg>
          </div>
          <span class="badge-number">{{ stage.number }}</span>
        </div>
        <div class="stage-content">
          <span class="stage-name">{{ stage.label }}</span>
          <span v-if="isStageCompleted(stage.id) && currentStage !== stage.id" class="status-icon">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 自定义 Toast 提示 -->
  <Transition name="toast">
    <div v-if="showToast" class="toast-notification" :class="`toast-${toastType}`">
      <svg v-if="toastType === 'warning'" class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 6V11M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <svg v-else class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 6V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 14H10.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="toast-message">{{ toastMessage }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  // 当前阶段: 1=标注, 2=排序, 3=翻译
  modelValue: {
    type: Number,
    default: 1
  },
  // 已完成的阶段列表
  completedStages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'stage-change'])

// 阶段配置
const stages = [
  { id: 1, number: '1', label: '标注' },
  { id: 2, number: '2', label: '排序' },
  { id: 3, number: '3', label: '翻译' }
]

const currentStage = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 提示消息状态
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('info') // 'info' | 'warning'

// 判断阶段是否已完成
const isStageCompleted = (stageId) => {
  return props.completedStages.includes(stageId)
}

// 判断阶段是否禁用（只有阶段1和阶段3默认可用，阶段2需要阶段1完成）
const isStageDisabled = (stageId) => {
  // 第一阶段永远可用
  if (stageId === 1) return false
  
  // 翻译阶段也默认可用（直接点击即可配置翻译）
  if (stageId === 3) return false
  
  // 排序阶段需要阶段1完成
  if (stageId === 2) {
    return !props.completedStages.includes(1)
  }
  
  return false
}

// 显示提示
const showToastMessage = (message, type = 'info') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  
  // 2秒后自动隐藏
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// 处理阶段点击
const handleStageClick = (stageId) => {
  if (isStageDisabled(stageId)) {
    // 只有阶段2可能被禁用
    if (stageId === 2) {
      showToastMessage('请先完成标注阶段', 'warning')
    }
    return
  }
  
  if (currentStage.value === stageId) {
    return // 当前阶段不需要切换
  }
  
  // 阶段3特殊处理：只触发事件，不改变currentStage
  if (stageId === 3) {
    emit('stage-change', stageId)
    return
  }
  
  // 其他阶段：正常切换
  currentStage.value = stageId
  emit('stage-change', stageId)
}
</script>

<style scoped lang="scss">
.stage-indicator {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  z-index: 999;
  
  .stage-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px) saturate(180%);
    border-radius: 28px 0 0 28px;
    padding: 16px 12px;
    box-shadow: 
      -10px 0 40px rgba(0, 0, 0, 0.08),
      -2px 0 10px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 72px;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    &:hover {
      width: 200px;
      padding-right: 24px;
      box-shadow: 
        -15px 0 50px rgba(0, 0, 0, 0.12),
        -4px 0 15px rgba(0, 0, 0, 0.08);
      
      .stage-content {
        opacity: 1;
        transform: translateX(0);
      }
    }
  }
  
  .stage-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:not(.is-disabled):hover {
      transform: translateX(-4px);
      
      .stage-badge {
        transform: scale(1.1);
      }
    }
    
    &.is-disabled {
      cursor: not-allowed;
      opacity: 0.4;
      
      &:hover {
        transform: none;
      }
      
      .stage-badge {
        background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
      
      .badge-number {
        color: #999999;
      }
    }
    
    // 活跃状态
    &.is-active {
      .stage-badge {
        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
        box-shadow: 
          0 4px 20px rgba(64, 158, 255, 0.4),
          0 0 0 4px rgba(64, 158, 255, 0.1);
        animation: pulse 2s ease-in-out infinite;
      }
      
      .badge-number {
        color: #ffffff;
        font-weight: 700;
      }
      
      .progress-ring-circle {
        stroke: rgba(255, 255, 255, 0.5);
        stroke-dashoffset: 0;
      }
      
      .stage-name {
        color: #409eff;
        font-weight: 600;
      }
    }
    
    // 完成状态
    &.is-completed:not(.is-active) {
      .stage-badge {
        background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
        box-shadow: 
          0 4px 16px rgba(103, 194, 58, 0.3),
          0 0 0 3px rgba(103, 194, 58, 0.08);
      }
      
      .badge-number {
        color: #ffffff;
      }
      
      .progress-ring-circle {
        stroke: rgba(255, 255, 255, 0.6);
        stroke-dashoffset: 0;
      }
      
      .stage-name {
        color: #67c23a;
      }
      
      .status-icon {
        color: #67c23a;
      }
    }
  }
  
  .stage-badge {
    position: relative;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.08),
      inset 0 1px 2px rgba(255, 255, 255, 0.5);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    .badge-number {
      position: absolute;
      z-index: 2;
      font-size: 20px;
      font-weight: 600;
      color: #606266;
      transition: all 0.3s ease;
    }
    
    .progress-ring {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) rotate(-90deg);
      pointer-events: none;
      
      svg {
        display: block;
      }
      
      circle {
        fill: none;
        stroke-width: 2.5;
        stroke: transparent;
        stroke-linecap: round;
        stroke-dasharray: 163.36;
        stroke-dashoffset: 163.36;
        transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
      }
    }
  }
  
  .stage-content {
    display: flex;
    align-items: center;
    gap: 8px;
    opacity: 0;
    transform: translateX(-10px);
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    .stage-name {
      font-size: 15px;
      font-weight: 500;
      color: #303133;
      white-space: nowrap;
      transition: all 0.3s ease;
    }
    
    .status-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      animation: checkFadeIn 0.5s ease;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 
      0 4px 20px rgba(64, 158, 255, 0.4),
      0 0 0 4px rgba(64, 158, 255, 0.1);
  }
  50% {
    box-shadow: 
      0 4px 25px rgba(64, 158, 255, 0.5),
      0 0 0 8px rgba(64, 158, 255, 0.15);
  }
}

@keyframes checkFadeIn {
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

// Toast 提示样式
.toast-notification {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  
  .toast-icon {
    flex-shrink: 0;
  }
  
  .toast-message {
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
  }
  
  &.toast-warning {
    border: 1px solid rgba(230, 162, 60, 0.3);
    
    .toast-icon {
      color: #e6a23c;
    }
    
    .toast-message {
      color: #e6a23c;
    }
  }
  
  &.toast-info {
    border: 1px solid rgba(64, 158, 255, 0.3);
    
    .toast-icon {
      color: #409eff;
    }
    
    .toast-message {
      color: #409eff;
    }
  }
}

// Toast 动画
.toast-enter-active {
  animation: toastSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  animation: toastSlideOut 0.25s ease;
}

@keyframes toastSlideIn {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes toastSlideOut {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px) scale(0.95);
  }
}
</style>
