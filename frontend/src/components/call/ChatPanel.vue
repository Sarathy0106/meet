<template>
  <div class="w-full h-full flex flex-col bg-[#202124] border-l border-meet-border text-meet-text select-text">
    <!-- Header -->
    <div class="px-4 sm:px-5 py-4 border-b border-meet-border flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button
          @click="meetingStore.closePanel()"
          class="md:hidden p-1.5 rounded-full hover:bg-meet-surfaceLight text-white mr-1"
          title="Back to call"
        >
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-medium text-white">In-call messages</h2>
      </div>
      <button
        @click="meetingStore.closePanel()"
        class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
        title="Close"
      >
        <X :size="20" />
      </button>
    </div>

    <!-- Notice banner -->
    <div class="px-4 py-3 mx-4 my-3 bg-[#303134] rounded-lg text-xs text-meet-textMuted flex items-start gap-2">
      <Info :size="16" class="shrink-0 mt-0.5 text-meet-primary" />
      <span>Messages can be seen only by people in the call and are saved for meeting history.</span>
    </div>

    <!-- Messages Container -->
    <div ref="messagesContainerRef" class="flex-1 overflow-y-auto px-4 py-2 space-y-4">
      <div
        v-if="chatStore.messages.length === 0"
        class="h-full flex flex-col items-center justify-center text-center text-meet-textMuted py-8"
      >
        <MessageSquare :size="36" class="mb-2 text-meet-border" />
        <p class="text-sm">No messages yet.</p>
        <p class="text-xs text-meet-textMuted">Send a message to everyone in the meeting.</p>
      </div>

      <div
        v-for="msg in chatStore.messages"
        :key="msg.id"
        class="flex flex-col"
        :class="{ 'items-end': msg.is_local }"
      >
        <div class="flex items-baseline gap-2 mb-1">
          <span class="text-xs font-semibold text-white">
            {{ msg.sender_name }} {{ msg.is_local ? '(You)' : '' }}
          </span>
          <span class="text-[10px] text-meet-textMuted">
            {{ formatTime(msg.sent_at) }}
          </span>
        </div>
        <div
          class="max-w-[85%] px-3.5 py-2 rounded-2xl text-sm break-words whitespace-pre-wrap shadow-sm"
          :class="
            msg.is_local
              ? 'bg-meet-blue text-white rounded-br-none'
              : 'bg-[#303134] text-meet-text rounded-bl-none'
          "
        >
          {{ msg.content }}
        </div>
      </div>
    </div>

    <!-- Input Bar -->
    <div class="p-4 border-t border-meet-border">
      <form @submit.prevent="sendMessage" class="flex items-center gap-2">
        <input
          v-model="inputContent"
          type="text"
          placeholder="Send a message to everyone"
          maxlength="5000"
          class="flex-1 px-4 py-2.5 bg-[#303134] border border-transparent focus:border-meet-primary rounded-full text-sm text-white placeholder-meet-textMuted outline-none transition-colors"
        />
        <button
          type="submit"
          :disabled="!inputContent.trim()"
          class="p-2.5 rounded-full bg-meet-blue hover:bg-meet-blue-hover disabled:bg-meet-surfaceLight disabled:text-meet-textMuted text-white transition-colors"
          title="Send message"
        >
          <Send :size="18" />
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { X, Info, Send, MessageSquare, ArrowLeft } from 'lucide-vue-next'
import { useMeetingStore } from '@/stores/meeting'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { livekitManager } from '@/lib/livekit'
import type { ChatMessage } from '@/types'

const meetingStore = useMeetingStore()
const chatStore = useChatStore()
const authStore = useAuthStore()

const inputContent = ref('')
const messagesContainerRef = ref<HTMLElement | null>(null)

function formatTime(isoString?: string) {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const content = inputContent.value.trim()
  if (!content || !meetingStore.currentMeeting) return

  const senderName = authStore.displayName
  const msgId = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
  const now = new Date().toISOString()

  const localMsg: ChatMessage = {
    id: msgId,
    meeting_id: meetingStore.currentMeeting.id,
    sender_name: senderName,
    content,
    sent_at: now,
    is_local: true,
  }

  // 1. Add locally
  chatStore.addMessage(localMsg)
  inputContent.value = ''
  scrollToBottom()

  // 2. Broadcast over LiveKit data channel
  await livekitManager.sendData({
    type: 'chat',
    senderName,
    payload: {
      id: msgId,
      content,
      sent_at: now,
    },
  })

  // 3. Persist to DB for history
  await chatStore.persistMessage(meetingStore.currentMeeting.code, content, senderName)
}

watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  }
)

onMounted(() => {
  scrollToBottom()
})
</script>
