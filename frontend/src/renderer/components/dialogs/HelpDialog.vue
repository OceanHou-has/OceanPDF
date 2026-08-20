<template>
  <el-dialog
    v-model="dialogVisible"
    width="880px"
    :close-on-click-modal="false"
    :show-header="false"
    :show-close="false"
    class="help-dialog"
  >
    <div class="cartoon-wrap">
      <!-- 装饰气泡 -->
      <div class="deco-bubbles" aria-hidden="true">
        <span class="bubble b1"></span>
        <span class="bubble b2"></span>
        <span class="bubble b3"></span>
        <span class="bubble b4"></span>
      </div>

      <!-- 自定义标题 -->
      <div class="dialog-header">
        <div class="header-deco" aria-hidden="true">
          <span class="star s1">✦</span>
          <span class="star s2">✧</span>
        </div>
        <div class="header-content">
          <div class="mascot">🐳</div>
          <div class="header-text">
            <h2 class="header-title">帮助中心</h2>
            <p class="header-subtitle">跟着图示一步步，快速申请并配置 API Key</p>
          </div>
        </div>
        <button class="close-btn" @click="dialogVisible = false" title="关闭">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- 子页切换 -->
      <div class="help-tabs">
        <button
          class="tab-pill tab-deepseek"
          :class="{ active: activeTab === 'deepseek' }"
          @click="activeTab = 'deepseek'"
        >
          <span class="tab-emoji">🐬</span>
          <span class="tab-text">
            <span class="tab-name">DeepSeek API Key</span>
            <span class="tab-sub">用于 AI 翻译</span>
          </span>
        </button>
        <button
          class="tab-pill tab-glm"
          :class="{ active: activeTab === 'glm' }"
          @click="activeTab = 'glm'"
        >
          <span class="tab-emoji">🐠</span>
          <span class="tab-text">
            <span class="tab-name">智谱 GLM API Key</span>
            <span class="tab-sub">用于文档解析 (GLM-OCR)</span>
          </span>
        </button>
      </div>

      <!-- 步骤内容 -->
      <div class="help-body">
        <transition name="tab-fade" mode="out-in">
          <div class="step-list" :key="activeTab">
            <div class="step-card" v-for="(step, index) in currentSteps" :key="step.title">
              <div class="step-index">{{ index + 1 }}</div>
              <div class="step-main">
                <h4 class="step-title">{{ step.title }}</h4>
                <p class="step-desc">{{ step.desc }}</p>
              </div>
              <el-image
                class="step-image"
                :src="step.img"
                :preview-src-list="previewList"
                :initial-index="index"
                preview-teleported
                fit="contain"
                loading="lazy"
              >
                <template #error>
                  <div class="image-error">
                    <span>🌊</span>
                    <p>图片加载失败</p>
                  </div>
                </template>
              </el-image>
            </div>
            <p class="zoom-tip">💡 点击任意图片可放大查看细节，支持左右翻页</p>
          </div>
        </transition>
      </div>

      <!-- 底部 -->
      <div class="dialog-footer">
        <button class="footer-btn" @click="dialogVisible = false">知道啦 🎉</button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'

// DeepSeek 图文步骤（按实际操作顺序组织）
import dsEnterPlatform from '../../../help/deepseekAPI/2-点击api开放平台.png'
import dsCreateKey from '../../../help/deepseekAPI/1-充值并生成apikey.png'
import dsFillKey from '../../../help/deepseekAPI/3-将apikey填入即可.png'

// 智谱 GLM 图文步骤
import glmEnterSite from '../../../help/GLMAPI/1-点击进入GLM官网.png'
import glmSaleZone from '../../../help/GLMAPI/2-点击进入特惠专区.png'
import glmBuyPlan from '../../../help/GLMAPI/3-购买这个2.9的套餐.png'
import glmConsole from '../../../help/GLMAPI/4-点击控制台.png'
import glmCreateKey from '../../../help/GLMAPI/5-申请一个apikey.png'
import glmFillKey from '../../../help/GLMAPI/6-粘贴进来即可.png'

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

const helpTabs = {
  deepseek: [
    {
      title: '进入 API 开放平台',
      desc: '访问 DeepSeek 官网（platform.deepseek.com），注册并登录账号后，点击首页的「API 开放平台」卡片进入开发者平台。',
      img: dsEnterPlatform
    },
    {
      title: '充值并生成 API Key',
      desc: '在开放平台左侧点击「API keys」，新建一个密钥并复制；余额不足时点击「去充值」按需充值少量金额（按量计费，足够翻译多篇论文）。',
      img: dsCreateKey
    },
    {
      title: '填入 OceanPDF',
      desc: '回到本应用「设置 → 翻译设置」，选择 DeepSeek 厂商，把 API Key 粘贴到密钥输入框，点击「测试连接」成功后即可保存使用。',
      img: dsFillKey
    }
  ],
  glm: [
    {
      title: '前往智谱官网',
      desc: '在本应用「设置 → 文档解析服务」中选择「智谱 GLM-OCR」，点击「申请 API Key」按钮即可跳转到智谱 BigModel 官网。',
      img: glmEnterSite
    },
    {
      title: '进入特惠专区',
      desc: '在官网顶部导航栏点击「定价」，在弹出的下拉菜单中选择「特惠专区」。',
      img: glmSaleZone
    },
    {
      title: '抢购 2.9 元新人套餐',
      desc: '找到「GLM-OCR」文档解析秒杀卡片（5000 万 tokens / 有效期 3 个月，仅需 ¥2.9），点击「去抢购」完成购买。',
      img: glmBuyPlan
    },
    {
      title: '进入控制台',
      desc: '购买完成后，点击官网右上角的「控制台」进入开发者控制台。',
      img: glmConsole
    },
    {
      title: '创建 API Key',
      desc: '在左侧「API 平台 → API Key」页面，点击右上角「+ 新建API Key」创建密钥，然后点击复制图标把它复制下来。',
      img: glmCreateKey
    },
    {
      title: '粘贴进 OceanPDF',
      desc: '回到本应用的 GLM-OCR 配置页，把 API Key 粘贴到输入框，点击「测试连接」验证通过后保存配置，上传翻译时会自动使用。',
      img: glmFillKey
    }
  ]
}

const activeTab = ref('deepseek')

const currentSteps = computed(() => helpTabs[activeTab.value])

const previewList = computed(() => currentSteps.value.map((s) => s.img))
</script>

<style scoped lang="scss">
// ===== 卡通海洋风配色（与翻译配置弹窗保持一致） =====
$ink: #3d5a73;
$sub-ink: #8aa2b8;
$blue: #58b6f0;
$blue-dark: #2e8bc7;
$green: #6fce93;
$orange: #ffb45d;
$pink: #ff9eb5;
$purple: #b3a4f3;
$yellow: #ffd97d;
$line: #e8f1f8;

.cartoon-wrap {
  position: relative;
  background:
    radial-gradient(circle at 20% 15%, #eaf7ff 0 2px, transparent 2px),
    radial-gradient(circle at 70% 40%, #eaf7ff 0 2px, transparent 2px),
    radial-gradient(circle at 45% 80%, #eaf7ff 0 2px, transparent 2px),
    linear-gradient(180deg, #fdfeff 0%, #f4fbff 100%);
  background-size: 90px 90px, 120px 120px, 100px 100px, 100% 100%;
  border-radius: 28px;
  border: 3px solid #cfe9fb;
  box-shadow: 0 12px 0 rgba(88, 182, 240, 0.16), 0 24px 60px rgba(46, 90, 122, 0.25);
  overflow: hidden;
  animation: pop-in 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes pop-in {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(16px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

// 装饰气泡
.deco-bubbles {
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 0;

  .bubble {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(160, 216, 248, 0.35));
    border: 2px solid rgba(140, 205, 245, 0.4);
    animation: bubble-float 5s ease-in-out infinite;
  }

  .b1 { width: 18px; height: 18px; right: 90px; top: 100px; animation-delay: 0s; }
  .b2 { width: 10px; height: 10px; right: 60px; top: 160px; animation-delay: 1.2s; }
  .b3 { width: 14px; height: 14px; left: 34px; bottom: 90px; animation-delay: 0.6s; }
  .b4 { width: 8px; height: 8px; left: 70px; bottom: 150px; animation-delay: 2s; }
}

@keyframes bubble-float {
  0%, 100% { transform: translateY(0); opacity: 0.8; }
  50% { transform: translateY(-10px); opacity: 1; }
}

// ===== 头部 =====
.dialog-header {
  position: relative;
  background: linear-gradient(135deg, #6fc7f5 0%, #4aa9ec 100%);
  padding: 18px 22px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;

  &::after {
    // 卡通波浪底边
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 14px;
    background:
      radial-gradient(circle at 10px -4px, transparent 0 12px, #fdfeff 12px) 0 0 / 28px 14px repeat-x;
  }

  .header-deco {
    position: absolute;
    inset: 0;
    pointer-events: none;

    .star {
      position: absolute;
      color: rgba(255, 255, 255, 0.9);
      animation: twinkle 2.2s ease-in-out infinite;
    }

    .s1 { right: 130px; top: 12px; font-size: 14px; }
    .s2 { right: 70px; top: 34px; font-size: 10px; animation-delay: 0.8s; }
  }

  .header-content {
    display: flex;
    align-items: center;
    gap: 14px;
    position: relative;
    z-index: 1;
  }

  .mascot {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.95);
    border: 3px solid #ffffff;
    box-shadow: 0 4px 0 rgba(46, 139, 199, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    animation: mascot-bounce 2.6s ease-in-out infinite;
  }

  .header-text {
    .header-title {
      font-size: 19px;
      font-weight: 800;
      color: #ffffff;
      margin: 0;
      letter-spacing: 2px;
      text-shadow: 0 2px 0 rgba(46, 139, 199, 0.45);
    }

    .header-subtitle {
      margin: 3px 0 0;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.9);
      letter-spacing: 0.5px;
    }
  }

  .close-btn {
    position: relative;
    z-index: 1;
    background: rgba(255, 255, 255, 0.25);
    border: 2px solid rgba(255, 255, 255, 0.6);
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #ffffff;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

    &:hover {
      background: #ffffff;
      color: #4aa9ec;
      transform: rotate(90deg) scale(1.1);
    }

    &:active {
      transform: rotate(90deg) scale(0.9);
    }
  }
}

@keyframes mascot-bounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  30% { transform: translateY(-5px) rotate(-6deg); }
  60% { transform: translateY(1px) rotate(4deg); }
}

@keyframes twinkle {
  0%, 100% { opacity: 0.4; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.2); }
}

// ===== 子页切换 =====
.help-tabs {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 14px;
  padding: 18px 22px 4px;

  .tab-pill {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 18px;
    border: 3px solid $line;
    background: #ffffff;
    cursor: pointer;
    text-align: left;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);

    .tab-emoji {
      width: 44px;
      height: 44px;
      flex: 0 0 auto;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      background: #f0f8ff;
      transition: transform 0.25s ease;
    }

    .tab-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;

      .tab-name {
        font-size: 15px;
        font-weight: 700;
        color: $ink;
        white-space: nowrap;
      }

      .tab-sub {
        font-size: 12px;
        color: $sub-ink;
        white-space: nowrap;
      }
    }

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(88, 182, 240, 0.18);
    }

    &:hover .tab-emoji {
      transform: scale(1.12) rotate(-6deg);
    }

    &.tab-deepseek.active {
      border-color: $blue;
      background: linear-gradient(135deg, #eaf7ff 0%, #d8f0ff 100%);
      box-shadow: 0 6px 0 rgba(88, 182, 240, 0.22), 0 10px 24px rgba(88, 182, 240, 0.25);

      .tab-emoji { background: #ffffff; }
      .tab-name { color: $blue-dark; }
    }

    &.tab-glm.active {
      border-color: $purple;
      background: linear-gradient(135deg, #f4f1ff 0%, #ebe5ff 100%);
      box-shadow: 0 6px 0 rgba(179, 164, 243, 0.25), 0 10px 24px rgba(179, 164, 243, 0.3);

      .tab-emoji { background: #ffffff; }
      .tab-name { color: #7a66d8; }
    }
  }
}

// ===== 步骤内容 =====
.help-body {
  position: relative;
  z-index: 1;
  padding: 14px 22px 4px;

  .step-list {
    max-height: 52vh;
    overflow-y: auto;
    padding-right: 6px;
    display: flex;
    flex-direction: column;
    gap: 14px;

    &::-webkit-scrollbar {
      width: 8px;
    }

    &::-webkit-scrollbar-thumb {
      background: #bfe3f8;
      border-radius: 4px;

      &:hover {
        background: #9dd4f3;
      }
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }
  }

  .step-card {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: #ffffff;
    border: 2px solid $line;
    border-radius: 20px;
    padding: 14px 16px;
    box-shadow: 0 4px 0 rgba(232, 241, 248, 0.9);
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 0 rgba(207, 233, 251, 0.9), 0 10px 22px rgba(88, 182, 240, 0.14);
    }

    .step-index {
      width: 34px;
      height: 34px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: linear-gradient(135deg, #6fc7f5 0%, #4aa9ec 100%);
      color: #ffffff;
      font-size: 16px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 3px 0 rgba(46, 139, 199, 0.4);
      margin-top: 2px;
    }

    .step-main {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;

      .step-title {
        margin: 0;
        font-size: 15px;
        font-weight: 700;
        color: $ink;
      }

      .step-desc {
        margin: 0;
        font-size: 13px;
        line-height: 1.7;
        color: $sub-ink;
      }
    }

    .step-image {
      flex: 0 0 300px;
      height: 180px;
      border-radius: 14px;
      border: 2px solid $line;
      background: #f7fbfe;
      overflow: hidden;
      cursor: zoom-in;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;

      &:hover {
        border-color: $blue;
        box-shadow: 0 6px 16px rgba(88, 182, 240, 0.25);
      }

      :deep(img) {
        transition: transform 0.3s ease;
      }

      &:hover :deep(img) {
        transform: scale(1.03);
      }
    }

    .image-error {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      color: $sub-ink;
      font-size: 12px;

      span {
        font-size: 26px;
      }

      p {
        margin: 0;
      }
    }
  }

  .zoom-tip {
    margin: 2px 2px 8px;
    font-size: 12px;
    color: $sub-ink;
    text-align: center;
  }
}

// 子页切换动画
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.tab-fade-enter-from {
  opacity: 0;
  transform: translateX(14px);
}

.tab-fade-leave-to {
  opacity: 0;
  transform: translateX(-14px);
}

// ===== 底部 =====
.dialog-footer {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  padding: 10px 22px 20px;

  .footer-btn {
    border: none;
    cursor: pointer;
    padding: 11px 44px;
    border-radius: 999px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #ffffff;
    background: linear-gradient(135deg, #6fc7f5 0%, #4aa9ec 100%);
    box-shadow: 0 5px 0 rgba(46, 139, 199, 0.55), 0 10px 20px rgba(88, 182, 240, 0.35);
    transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 7px 0 rgba(46, 139, 199, 0.55), 0 14px 26px rgba(88, 182, 240, 0.4);
    }

    &:active {
      transform: translateY(3px);
      box-shadow: 0 2px 0 rgba(46, 139, 199, 0.55), 0 6px 12px rgba(88, 182, 240, 0.3);
    }
  }
}
</style>

<style lang="scss">
.help-dialog.el-dialog {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  overflow: visible;
  border: none;
  // 保留 Element Plus 默认定位，避免弹窗贴顶
  margin: var(--el-dialog-margin-top, 12vh) auto 50px;
  outline: none;

  .el-dialog__header,
  .el-dialog__footer {
    padding: 0;
    margin: 0;
    background: transparent;
  }

  .el-dialog__body {
    padding: 0;
    background: transparent;
  }
}

.el-overlay:has(.help-dialog) {
  background-color: rgba(46, 90, 122, 0.45);
  backdrop-filter: blur(3px);
}
</style>
