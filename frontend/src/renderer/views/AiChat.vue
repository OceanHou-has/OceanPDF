<template>
  <div class="ai-chat">
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
          <span class="subtitle">AI 论文问答</span>
        </div>
      </div>
      <div class="navbar-right">
        <Button1
          class="nav-btn clear-btn"
          size="icon"
          :disabled="messages.length === 0"
          @click="handleClear"
          aria-label="清空对话"
          title="清空对话"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Button1>
      </div>
    </div>

    <!-- 聊天消息区 -->
    <div class="chat-body" ref="chatBody">
      <div v-if="messages.length === 0" class="empty-tip">
        <div class="empty-icon">💬</div>
        <p>针对这篇论文提问，例如：</p>
        <p class="example">“这篇论文主要解决了什么问题？”</p>
        <p class="example">“核心方法是什么？有什么创新点？”</p>
        <p class="example">“实验结论有哪些？有什么局限？”</p>
      </div>

      <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="msg.role">
        <div class="avatar" :class="msg.role">
          {{ msg.role === 'user' ? '我' : 'AI' }}
        </div>
        <div class="bubble" :class="msg.role">
          <span v-if="msg.content">{{ msg.content }}</span>
          <span v-else-if="msg.role === 'assistant'" class="typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </span>
        </div>
      </div>
    </div>

    <!-- 底部输入区 -->
    <div class="chat-input-bar">
      <el-input
        v-model="input"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :placeholder="loading ? 'AI 正在思考…' : '输入你的问题，回车发送（Shift+Enter 换行）'"
        :disabled="loading"
        resize="none"
        @keydown="handleKeydown"
      />
      <button class="send-btn" :disabled="loading || !input.trim()" @click="send">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button1 from '../elements/button/button1.vue'

const route = useRoute()
const router = useRouter()

const pdfName = ref(route.query.pdfName || '未命名论文')
const input = ref('')
const loading = ref(false)
const messages = ref([])      // 展示用：{ role: 'user' | 'assistant', content }
const history = ref([])       // 回传后端的历史对话：{ role, content }
const chatBody = ref(null)

const API_URL = 'http://127.0.0.1:8000/api/v1/qa/ask'

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}

const handleBack = () => {
  router.back()
}

const handleClear = () => {
  messages.value = []
  history.value = []
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

// 解析单帧 SSE（data: {...}）
const parseFrame = (frame) => {
  const lines = frame.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed.startsWith('data:')) continue
    const payload = trimmed.slice(5).trim()
    if (!payload) continue
    try {
      return JSON.parse(payload)
    } catch (e) {
      // 忽略无法解析的帧
    }
  }
  return null
}

const send = async () => {
  const question = input.value.trim()
  if (!question || loading.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: question })
  messages.value.push({ role: 'assistant', content: '' })
  // 通过数组下标访问 reactive 元素，才能触发视图响应式更新
  const aiIndex = messages.value.length - 1
  scrollToBottom()

  // 请求携带本轮之前的历史
  const reqHistory = history.value.slice()
  history.value.push({ role: 'user', content: question })

  loading.value = true
  let full = ''

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pdf_name: pdfName.value,
        question,
        history: reqHistory
      })
    })

    if (!res.ok || !res.body) {
      throw new Error(`请求失败 (${res.status})`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        const data = parseFrame(frame)
        if (!data) continue

        if (data.type === 'delta') {
          full += data.content || ''
          messages.value[aiIndex].content = full
          scrollToBottom()
        } else if (data.type === 'done') {
          // 正常结束
        } else if (data.type === 'error') {
          throw new Error(data.message || '回答失败')
        }
      }
    }

    if (!full) {
      messages.value[aiIndex].content = '（未收到回答）'
    }
    history.value.push({ role: 'assistant', content: messages.value[aiIndex].content })
  } catch (e) {
    messages.value[aiIndex].content = '⚠️ 出错了：' + (e.message || String(e))
    history.value.push({ role: 'assistant', content: messages.value[aiIndex].content })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped lang="scss">
.ai-chat {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

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
      max-width: 60vw;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
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
  }
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;

  &::-webkit-scrollbar {
    width: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background: #c0c4cc;
    border-radius: 4px;
  }
}

.empty-tip {
  margin: auto;
  text-align: center;
  color: #909399;
  font-size: 14px;

  .empty-icon {
    font-size: 40px;
    margin-bottom: 12px;
  }

  .example {
    color: #b0b3b8;
    font-size: 13px;
    margin-top: 4px;
  }
}

.message-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;

  &.user {
    flex-direction: row-reverse;
  }
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;

  &.user {
    background: #409eff;
    color: white;
  }

  &.assistant {
    background: #67c23a;
    color: white;
  }
}

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;

  &.user {
    background: #409eff;
    color: white;
    border-top-right-radius: 4px;
  }

  &.assistant {
    background: white;
    color: #303133;
    border: 1px solid #e4e7ed;
    border-top-left-radius: 4px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  }
}

.typing {
  display: inline-flex;
  gap: 4px;
  align-items: center;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #c0c4cc;
    animation: blink 1.2s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes blink {
  0%, 80%, 100% {
    opacity: 0.3;
  }
  40% {
    opacity: 1;
  }
}

.chat-input-bar {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #e4e7ed;

  :deep(.el-textarea__inner) {
    font-size: 14px;
    border-radius: 12px;
    padding: 12px 16px;
    line-height: 1.6;
  }
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  border: none;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: #66b1ff;
  }

  &:disabled {
    background: #c0c4cc;
    cursor: not-allowed;
  }
}
</style>
