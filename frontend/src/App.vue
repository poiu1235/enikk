<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'
import { NConfigProvider } from 'naive-ui'
import { useChatStore } from './stores/chat'
import ChatPanel from './components/ChatPanel.vue'

const chat = useChatStore()

onMounted(() => {
  chat.connect()
})

onBeforeUnmount(() => {
  chat.disconnect()
})
</script>

<template>
  <NConfigProvider>
    <ChatPanel />
  </NConfigProvider>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
