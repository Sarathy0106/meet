import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type { ChatMessage } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const unreadCount = ref<number>(0)
  const isChatOpen = ref<boolean>(false)

  function addMessage(msg: ChatMessage) {
    // Avoid duplicates by ID or timestamp+content
    const exists = messages.value.some((m) => m.id === msg.id)
    if (!exists) {
      messages.value.push(msg)
      if (!isChatOpen.value && !msg.is_local) {
        unreadCount.value++
      }
    }
  }

  function openChat() {
    isChatOpen.value = true
    unreadCount.value = 0
  }

  function closeChat() {
    isChatOpen.value = false
  }

  function toggleChat() {
    if (isChatOpen.value) {
      closeChat()
    } else {
      openChat()
    }
  }

  async function loadHistory(meetingCode: string) {
    try {
      const res = await api.get(`/meetings/${meetingCode}/chat`)
      messages.value = res.data
    } catch (e) {
      console.warn('Failed to load chat history:', e)
    }
  }

  async function persistMessage(meetingCode: string, content: string, senderName: string) {
    try {
      const res = await api.post(`/meetings/${meetingCode}/chat`, {
        content,
        sender_name: senderName,
      })
      return res.data
    } catch (e) {
      console.warn('Failed to persist chat message:', e)
      return null
    }
  }

  function clearMessages() {
    messages.value = []
    unreadCount.value = 0
    isChatOpen.value = false
  }

  return {
    messages,
    unreadCount,
    isChatOpen,
    addMessage,
    openChat,
    closeChat,
    toggleChat,
    loadHistory,
    persistMessage,
    clearMessages,
  }
})
