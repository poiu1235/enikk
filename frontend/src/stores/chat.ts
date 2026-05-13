import { defineStore } from 'pinia'
import { ref } from 'vue'
import { WsClient } from '../ws-client'
import type { WsEvent } from '../ws-client'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  runId?: string
  streaming?: boolean
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const wsClient = new WsClient({
    url: import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:18932',
    onEvent: handleEvent,
  })
  const connected = ref(false)
  const currentRunId = ref('')

  function connect() {
    wsClient.connect()
  }

  function disconnect() {
    wsClient.disconnect()
  }

  async function send(content: string) {
    try {
      messages.value.push({
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      })

      const result = await wsClient.chatSend(content)
      currentRunId.value = result.runId

      // Add assistant placeholder for streaming
      messages.value.push({
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        runId: result.runId,
        streaming: true,
      })
    } catch (e) {
      console.error('Failed to send message:', e)
    }
  }

  async function abort() {
    if (currentRunId.value) {
      await wsClient.chatAbort(currentRunId.value)
      // Mark streaming message as done
      const last = messages.value[messages.value.length - 1]
      if (last?.streaming) {
        last.streaming = false
      }
      currentRunId.value = ''
    }
  }

  function handleEvent(event: WsEvent) {
    switch (event.type) {
      case 'agent.started':
        // Agent started
        break
      case 'agent.event':
        // Append streaming text
        if (event.runId && messages.value.length > 0) {
          const last = messages.value[messages.value.length - 1]
          if (last.role === 'assistant' && last.runId === event.runId) {
            last.content += event.text || ''
          }
        }
        break
      case 'agent.done':
        // Mark as done
        const doneMsg = messages.value.find(m => m.runId === event.runId && m.streaming)
        if (doneMsg) {
          doneMsg.streaming = false
          if (event.text && !doneMsg.content) {
            doneMsg.content = event.text
          }
        }
        currentRunId.value = ''
        break
      case 'agent.error':
        const errMsg = messages.value.find(m => m.runId === event.runId && m.streaming)
        if (errMsg) {
          errMsg.content = `❌ Error: ${event.error || 'Unknown error'}`
          errMsg.streaming = false
        }
        currentRunId.value = ''
        break
      case 'agent.aborted':
        const abortMsg = messages.value.find(m => m.runId === event.runId && m.streaming)
        if (abortMsg) {
          abortMsg.content += '\n\n⏹ 已中断'
          abortMsg.streaming = false
        }
        currentRunId.value = ''
        break
    }
  }

  // WebSocket connection state
  wsClient.onConnected = () => { connected.value = true }
  wsClient.onDisconnected = () => { connected.value = false }

  return {
    messages,
    connected,
    currentRunId,
    connect,
    disconnect,
    send,
    abort,
  }
})
