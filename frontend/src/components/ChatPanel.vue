<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { NInput, NButton, NScrollbar, NTag, NSpace } from 'naive-ui'

const chat = useChatStore()
const input = ref('')
const scrollRef = ref<InstanceType<typeof NScrollbar> | null>(null)

async function handleSend() {
  const text = input.value.trim()
  if (!text) return
  input.value = ''
  await chat.send(text)
  await nextTick()
  scrollRef.value?.scrollTo({ top: 999999, behavior: 'smooth' })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-panel">
    <!-- Header -->
    <div class="chat-header">
      <span class="title">💬 Enikk Chat</span>
      <NTag :type="chat.connected ? 'success' : 'warning'" size="small">
        {{ chat.connected ? 'Connected' : 'Disconnected' }}
      </NTag>
    </div>

    <!-- Messages -->
    <NScrollbar ref="scrollRef" class="messages">
      <div v-if="chat.messages.length === 0" class="empty">
        <p>发送消息给 NIKKE Agent</p>
        <p class="hint">例如: "完成每日任务"</p>
      </div>
      <div
        v-for="(msg, i) in chat.messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="bubble">
          <pre v-if="msg.role === 'user'">{{ msg.content }}</pre>
          <div v-else class="assistant-content">
            <span>{{ msg.content }}</span>
            <span v-if="msg.streaming" class="cursor">▊</span>
          </div>
        </div>
      </div>
    </NScrollbar>

    <!-- Input -->
    <div class="input-area">
      <NInput
        v-model:value="input"
        type="textarea"
        placeholder="输入指令..."
        :autosize="{ minRows: 1, maxRows: 4 }"
        @keydown="handleKeydown"
        :disabled="chat.currentRunId !== ''"
      />
      <NSpace class="buttons">
        <NButton
          v-if="chat.currentRunId"
          type="error"
          secondary
          @click="chat.abort()"
        >
          中断
        </NButton>
        <NButton
          type="primary"
          :disabled="!input.trim() || chat.currentRunId !== ''"
          @click="handleSend"
        >
          发送
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fafafa;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
}

.chat-header .title {
  font-weight: 600;
  font-size: 16px;
}

.messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.empty {
  text-align: center;
  color: #999;
  margin-top: 40%;
}

.empty .hint {
  font-size: 12px;
  margin-top: 8px;
}

.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.message.user .bubble {
  background: #DCF8C6;
}

.message.user .bubble pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.assistant .bubble {
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.assistant-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor {
  animation: blink 1s step-end infinite;
  color: #999;
}

@keyframes blink {
  50% { opacity: 0; }
}

.input-area {
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.buttons {
  flex-shrink: 0;
}
</style>
