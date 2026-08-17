<template>
  <Transition name="toast">
    <div v-if="visible" class="toast-notification" :class="`toast-${type}`">
      <svg v-if="type === 'success'" class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M6 10L9 13L14 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <svg v-else-if="type === 'error'" class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M13 7L7 13M7 7L13 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <svg v-else-if="type === 'warning'" class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 6V11M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <svg v-else class="toast-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 19C14.9706 19 19 14.9706 19 10C19 5.02944 14.9706 1 10 1C5.02944 1 1 5.02944 1 10C1 14.9706 5.02944 19 10 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 6V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10 14H10.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="toast-message">{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'

const visible = ref(false)
const message = ref('')
const type = ref('info')
let timer = null

const show = (msg, msgType = 'info', duration = 2000) => {
  message.value = msg
  type.value = msgType
  visible.value = true
  
  if (timer) {
    clearTimeout(timer)
  }
  
  timer = setTimeout(() => {
    visible.value = false
  }, duration)
}

defineExpose({
  show
})
</script>

<style scoped lang="scss">
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
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  &.toast-success {
    border: 1px solid rgba(103, 194, 58, 0.3);
    
    .toast-icon {
      color: #67c23a;
    }
    
    .toast-message {
      color: #67c23a;
    }
  }
  
  &.toast-error {
    border: 1px solid rgba(245, 108, 108, 0.3);
    
    .toast-icon {
      color: #f56c6c;
    }
    
    .toast-message {
      color: #f56c6c;
    }
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
