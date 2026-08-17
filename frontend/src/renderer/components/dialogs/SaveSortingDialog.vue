<template>
  <el-dialog
    v-model="dialogVisible"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    width="480px"
    align-center
    class="save-sorting-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <div class="icon-wrapper">
          <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  stroke="currentColor" 
                  stroke-width="2" 
                  stroke-linecap="round" 
                  stroke-linejoin="round"/>
          </svg>
        </div>
        <h3 class="dialog-title">保存排序</h3>
      </div>
    </template>
    
    <div class="dialog-content">
      <p class="message">
        检测到未保存的排序，是否保存当前排序结果？
      </p>
      <div class="info-box">
        <svg class="info-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                stroke="currentColor" 
                stroke-width="2" 
                stroke-linecap="round" 
                stroke-linejoin="round"/>
        </svg>
        <span>未设置的元素将自动按默认顺序排列</span>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <button class="btn btn-cancel" @click="handleCancel">
          <span>取消操作</span>
        </button>
        <button class="btn btn-discard" @click="handleDiscard">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 18L18 6M6 6l12 12" 
                  stroke="currentColor" 
                  stroke-width="2" 
                  stroke-linecap="round" 
                  stroke-linejoin="round"/>
          </svg>
          <span>不保存</span>
        </button>
        <button class="btn btn-save" @click="handleSave">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 13l4 4L19 7" 
                  stroke="currentColor" 
                  stroke-width="2" 
                  stroke-linecap="round" 
                  stroke-linejoin="round"/>
          </svg>
          <span>保存排序</span>
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'cancel', 'discard', 'save'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleCancel = () => {
  emit('cancel')
}

const handleDiscard = () => {
  emit('discard')
}

const handleSave = () => {
  emit('save')
}
</script>

<style scoped lang="scss">
.save-sorting-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    padding: 0;
    overflow: hidden;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 
      0 20px 60px rgba(102, 126, 234, 0.3),
      0 0 0 1px rgba(255, 255, 255, 0.1);
  }
  
  :deep(.el-dialog__header) {
    padding: 0;
    margin: 0;
  }
  
  :deep(.el-dialog__body) {
    padding: 0 32px 24px;
    background: white;
  }
  
  :deep(.el-dialog__footer) {
    padding: 0 32px 32px;
    background: white;
  }
}

.dialog-header {
  padding: 32px 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .icon-wrapper {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    
    .icon {
      width: 36px;
      height: 36px;
      color: white;
    }
  }
  
  .dialog-title {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: white;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}

.dialog-content {
  .message {
    margin: 0 0 16px;
    font-size: 16px;
    line-height: 1.6;
    color: #303133;
    text-align: center;
  }
  
  .info-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #e0e7ff 0%, #e9d5ff 100%);
    border-radius: 8px;
    border: 1px solid rgba(139, 92, 246, 0.2);
    
    .info-icon {
      width: 20px;
      height: 20px;
      color: #8b5cf6;
      flex-shrink: 0;
    }
    
    span {
      font-size: 14px;
      color: #6b21a8;
      line-height: 1.5;
    }
  }
}

.dialog-footer {
  display: flex;
  gap: 12px;
  
  .btn {
    flex: 1;
    height: 44px;
    border-radius: 8px;
    border: none;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    
    .btn-icon {
      width: 18px;
      height: 18px;
    }
    
    &:active {
      transform: scale(0.95);
    }
    
    &.btn-cancel {
      background: #f5f5f5;
      color: #606266;
      border: 1px solid #e4e7ed;
      
      &:hover {
        background: #e9e9e9;
        border-color: #d0d3d9;
      }
    }
    
    &.btn-discard {
      background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
      color: #dc2626;
      border: 1px solid rgba(220, 38, 38, 0.2);
      
      &:hover {
        background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
      }
    }
    
    &.btn-save {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
      
      &:hover {
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
      }
      
      &:active {
        transform: translateY(0) scale(0.95);
      }
    }
  }
}
</style>
