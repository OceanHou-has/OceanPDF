<template>
  <el-dialog
    v-model="dialogVisible"
    width="640px"
    :close-on-click-modal="false"
    :show-header="false"
    :show-close="false"
    class="developer-dialog"
  >
    <div class="dev-wrap">
      <!-- 自定义标题 -->
      <div class="dialog-header">
        <div class="header-mascot" aria-hidden="true">
          <img class="mascot-icon" :src="devIcon" alt="" />
        </div>
        <div class="header-text">
          <h2 class="header-title">开发者信息</h2>
          <p class="header-subtitle">感谢使用 OceanPDF，欢迎交流反馈</p>
        </div>
        <button class="close-btn" @click="dialogVisible = false" title="关闭" aria-label="关闭">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- 作者信息 -->
      <div class="author-card">
        <div class="author-avatar" aria-hidden="true">🐳</div>
        <div class="author-info">
          <div class="author-name">ocean</div>
          <div class="author-meta">中南大学在读硕士 · 扭曲丛林第一兰博🐶</div>
        </div>
      </div>

      <!-- 联系方式 -->
      <div class="contact-card">
        <div class="contact-label">📮 联系方式</div>
        <a class="contact-email" :href="`mailto:${email}`">{{ email }}</a>
      </div>

      <!-- 打赏栏目 -->
      <div class="donate-section">
        <h3 class="donate-title">🎁 打赏支持</h3>
        <p class="donate-tip">各位帅哥美女，觉得好用的话可以考虑打赏一波~</p>
        <div class="qr-list">
          <div class="qr-item">
            <el-image
              class="qr-image"
              :src="wechatQr"
              :preview-src-list="qrPreviewList"
              :initial-index="0"
              preview-teleported
              fit="contain"
              loading="lazy"
            >
              <template #error>
                <div class="qr-error">二维码加载失败</div>
              </template>
            </el-image>
            <span class="qr-name">微信</span>
          </div>
          <div class="qr-item">
            <el-image
              class="qr-image"
              :src="alipayQr"
              :preview-src-list="qrPreviewList"
              :initial-index="1"
              preview-teleported
              fit="contain"
              loading="lazy"
            >
              <template #error>
                <div class="qr-error">二维码加载失败</div>
              </template>
            </el-image>
            <span class="qr-name">支付宝</span>
          </div>
        </div>
        <p class="qr-tip">💡 点击二维码可放大查看</p>
      </div>

      <!-- 右下角彩蛋按钮 -->
      <button
        class="easter-btn"
        @click="uselessVisible = true"
        title="?"
        aria-label="隐藏彩蛋按钮"
      >
        <span>?</span>
      </button>
    </div>

    <!-- 彩蛋提示弹窗 -->
    <el-dialog
      v-model="uselessVisible"
      width="300px"
      :show-header="false"
      :close-on-click-modal="true"
      class="useless-dialog"
      append-to-body
    >
      <div class="useless-content">
        <div class="useless-icon" aria-hidden="true">🐋</div>
        <p class="useless-text">这个按钮并没有什么用~</p>
        <button class="useless-ok" @click="uselessVisible = false">知道了</button>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import wechatQr from '../../../help/gathering/weixinzhifu.jpg'
import alipayQr from '../../../help/gathering/zhifubao.jpg'
import devIcon from '../../elements/icon/开发者.svg'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 彩蛋弹窗
const uselessVisible = ref(false)

// 开发者信息
const email = '18734341769@163.com'
const qrPreviewList = [wechatQr, alipayQr]
</script>

<style scoped lang="scss">
.dev-wrap {
  position: relative;
  padding: 28px 32px 32px;
  background: linear-gradient(160deg, #F8FAFF 0%, #FFFFFF 55%, #FDF6FF 100%);
  border-radius: 12px;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 18px;
  border-bottom: 1px solid #EAECF3;

  .header-mascot {
    width: 52px;
    height: 52px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    background: linear-gradient(135deg, rgba(79, 107, 255, 0.12), rgba(139, 92, 246, 0.14));
    border-radius: 14px;

    .mascot-icon {
      width: 30px;
      height: 30px;
      display: block;
    }
  }

  .header-text {
    flex: 1;

    .header-title {
      font-size: 22px;
      font-weight: 700;
      color: #111827;
      margin: 0 0 4px 0;
    }

    .header-subtitle {
      font-size: 13px;
      color: #6B7280;
      margin: 0;
    }
  }

  .close-btn {
    width: 34px;
    height: 34px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 50%;
    background: #F3F4F6;
    color: #6B7280;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      background: #E5E7EB;
      color: #111827;
    }
  }
}

.author-card {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 22px;
  padding: 18px 20px;
  background: #FFFFFF;
  border: 1px solid #EAECF3;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(17, 24, 39, 0.05);

  .author-avatar {
    width: 56px;
    height: 56px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    background: linear-gradient(135deg, #4F6BFF 0%, #8B5CF6 100%);
    border-radius: 50%;
    box-shadow: 0 6px 16px rgba(79, 107, 255, 0.35);
  }

  .author-info {
    .author-name {
      font-size: 18px;
      font-weight: 700;
      color: #111827;
      margin-bottom: 4px;
    }

    .author-meta {
      font-size: 14px;
      color: #6B7280;
      line-height: 1.5;
    }
  }
}

.contact-card {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 14px 20px;
  background: #FFFFFF;
  border: 1px solid #EAECF3;
  border-radius: 14px;

  .contact-label {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
  }

  .contact-email {
    font-size: 15px;
    font-weight: 500;
    color: #4F6BFF;
    text-decoration: none;
    transition: opacity 0.2s ease;

    &:hover {
      opacity: 0.75;
      text-decoration: underline;
    }
  }
}

.donate-section {
  margin-top: 16px;
  padding: 18px 20px 20px;
  background: #FFFFFF;
  border: 1px solid #EAECF3;
  border-radius: 14px;
  text-align: center;

  .donate-title {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
    margin: 0 0 6px 0;
  }

  .donate-tip {
    font-size: 14px;
    color: #6B7280;
    margin: 0 0 18px 0;
    line-height: 1.6;
  }

  .qr-list {
    display: flex;
    justify-content: center;
    gap: 28px;

    .qr-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      .qr-image {
        width: 168px;
        height: 168px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        background: #FFFFFF;
        cursor: zoom-in;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(17, 24, 39, 0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(17, 24, 39, 0.12);
        }
      }

      .qr-name {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
      }
    }
  }

  .qr-error {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    color: #9CA3AF;
    background: #F9FAFB;
  }

  .qr-tip {
    margin: 14px 0 0 0;
    font-size: 12px;
    color: #9CA3AF;
  }
}

.easter-btn {
  position: absolute;
  right: 16px;
  bottom: 16px;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(79, 107, 255, 0.08);
  color: #9CA3AF;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #4F6BFF;
    color: #FFFFFF;
  }
}

.useless-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 18px 8px 8px;
  text-align: center;

  .useless-icon {
    font-size: 40px;
    line-height: 1;
  }

  .useless-text {
    margin: 0;
    font-size: 15px;
    color: #374151;
    line-height: 1.6;
  }

  .useless-ok {
    margin-top: 6px;
    padding: 8px 26px;
    border: none;
    border-radius: 20px;
    background: linear-gradient(135deg, #4F6BFF 0%, #8B5CF6 100%);
    color: #FFFFFF;
    font-size: 14px;
    cursor: pointer;
    transition: opacity 0.2s ease;

    &:hover {
      opacity: 0.85;
    }
  }
}
</style>
