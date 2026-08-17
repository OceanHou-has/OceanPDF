<template>
  <el-dialog
    v-model="dialogVisible"
    title="选择标注方式"
    width="500px"
    :before-close="handleClose"
  >
    <div class="dialog-content">
      <el-icon class="info-icon"><InfoFilled /></el-icon>
      <p class="message">您选择了 <span class="highlight">{{ selectedCount }}</span> 个元素框</p>
      <p class="sub-message">请选择标注方式：</p>
      
      <div class="option-cards">
        <div class="option-card" @click="handleMerge">
          <el-icon class="card-icon merge-icon"><Connection /></el-icon>
          <div class="card-title">合并标注</div>
          <div class="card-desc">将所有选中的元素合并为一个整体</div>
        </div>
        
        <div class="option-card" @click="handleSeparate">
          <el-icon class="card-icon separate-icon"><Grid /></el-icon>
          <div class="card-title">单独标注</div>
          <div class="card-desc">为每个元素分别标注类型</div>
        </div>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { InfoFilled, Connection, Grid } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  selectedCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue', 'merge', 'separate'])

const dialogVisible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  dialogVisible.value = false
}

const handleMerge = () => {
  emit('merge')
  dialogVisible.value = false
}

const handleSeparate = () => {
  emit('separate')
  dialogVisible.value = false
}
</script>

<style scoped lang="scss">
.dialog-content {
  text-align: center;
  padding: 20px 0;
  
  .info-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
  }
  
  .message {
    font-size: 16px;
    color: #303133;
    margin-bottom: 8px;
    
    .highlight {
      color: #409eff;
      font-weight: 600;
      font-size: 18px;
    }
  }
  
  .sub-message {
    font-size: 14px;
    color: #909399;
    margin-bottom: 24px;
  }
  
  .option-cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 20px;
  }
  
  .option-card {
    padding: 24px 16px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    background: #fafafa;
    
    &:hover {
      border-color: #409eff;
      background: white;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
    }
    
    .card-icon {
      font-size: 36px;
      margin-bottom: 12px;
      
      &.merge-icon {
        color: #67c23a;
      }
      
      &.separate-icon {
        color: #e6a23c;
      }
    }
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }
    
    .card-desc {
      font-size: 12px;
      color: #909399;
      line-height: 1.4;
    }
  }
}
</style>
