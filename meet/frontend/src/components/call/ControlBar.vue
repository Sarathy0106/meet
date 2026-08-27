<template>
  <div class="h-20 w-full px-3 sm:px-6 flex items-center justify-between z-30 select-none bg-[#202124]/90 backdrop-blur-md border-t border-white/5">
    <!-- Desktop Left Section: Meeting info & Local Time -->
    <div class="hidden md:flex items-center gap-3 w-1/4">
      <span class="text-sm font-medium text-meet-text tracking-wide">{{ currentTime }}</span>
      <span class="text-meet-textMuted text-xs">|</span>
      <button
        @click="copyCode"
        class="text-xs font-medium text-meet-textMuted hover:text-white flex items-center gap-1.5 transition-colors"
        :title="'Click to copy meeting code: ' + meetingCode"
      >
        <span>{{ meetingCode }}</span>
        <Copy :size="12" />
      </button>
    </div>

    <!-- Desktop Center Section / Mobile Primary Controls -->
    <div class="flex-1 md:flex-initial flex items-center justify-center gap-2 sm:gap-3">
      <!-- Microphone Toggle -->
      <button
        @click="$emit('toggle-mic')"
        class="relative p-3 sm:p-3.5 rounded-full transition-all duration-200 shadow-md"
        :class="
          isAudioEnabled
            ? 'bg-meet-surfaceLight hover:bg-meet-border text-white'
            : 'bg-meet-red hover:bg-meet-redHover text-white'
        "
        :title="isAudioEnabled ? 'Turn off microphone' : 'Turn on microphone'"
      >
        <Mic v-if="isAudioEnabled" :size="20" />
        <MicOff v-else :size="20" />
      </button>

      <!-- Camera Toggle -->
      <button
        @click="$emit('toggle-camera')"
        class="relative p-3 sm:p-3.5 rounded-full transition-all duration-200 shadow-md"
        :class="
          isVideoEnabled
            ? 'bg-meet-surfaceLight hover:bg-meet-border text-white'
            : 'bg-meet-red hover:bg-meet-redHover text-white'
        "
        :title="isVideoEnabled ? 'Turn off camera' : 'Turn on camera'"
      >
        <Video v-if="isVideoEnabled" :size="20" />
        <VideoOff v-else :size="20" />
      </button>

      <!-- Desktop Screen Share Toggle -->
      <button
        @click="$emit('toggle-screenshare')"
        class="hidden md:flex p-3 sm:p-3.5 rounded-full transition-all duration-200 shadow-md"
        :class="
          isScreenSharing
            ? 'bg-meet-primary text-gray-900 font-semibold'
            : 'bg-meet-surfaceLight hover:bg-meet-border text-white'
        "
        :title="isScreenSharing ? 'Stop presenting' : 'Present now'"
      >
        <ScreenShare :size="20" />
      </button>

      <!-- Desktop Raise Hand -->
      <button
        @click="$emit('toggle-hand')"
        class="hidden md:flex p-3 sm:p-3.5 rounded-full transition-all duration-200 shadow-md"
        :class="
          isHandRaised
            ? 'bg-meet-yellow text-gray-900 font-semibold animate-pulse'
            : 'bg-meet-surfaceLight hover:bg-meet-border text-white'
        "
        :title="isHandRaised ? 'Lower hand' : 'Raise hand'"
      >
        <Hand :size="20" />
      </button>

      <!-- Desktop Device Settings Modal Trigger -->
      <button
        @click="$emit('open-devices')"
        class="hidden md:flex p-3 sm:p-3.5 rounded-full bg-meet-surfaceLight hover:bg-meet-border text-white transition-all duration-200 shadow-md"
        title="Audio and video settings"
      >
        <Settings :size="20" />
      </button>

      <!-- Mobile Quick Chat Toggle Button (Visible on mobile screens) -->
      <button
        @click="handleToggleChat"
        class="flex md:hidden relative p-3 rounded-full transition-colors shadow-md"
        :class="
          meetingStore.activePanel === 'chat'
            ? 'bg-meet-primary text-gray-900'
            : 'bg-meet-surfaceLight hover:bg-meet-border text-white'
        "
        title="Chat"
      >
        <MessageSquare :size="20" />
        <span
          v-if="chatStore.unreadCount > 0"
          class="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-meet-red text-white text-[10px] font-bold flex items-center justify-center shadow"
        >
          {{ chatStore.unreadCount }}
        </span>
      </button>

      <!-- Mobile "More Options" Action Sheet Trigger -->
      <button
        @click="isMobileSheetOpen = true"
        class="flex md:hidden p-3 rounded-full bg-meet-surfaceLight hover:bg-meet-border text-white transition-colors shadow-md"
        title="More actions"
      >
        <MoreVertical :size="20" />
      </button>

      <!-- Leave / End Meeting (Red Button) -->
      <button
        @click="$emit('leave')"
        class="px-4 sm:px-6 py-3 rounded-full bg-meet-red hover:bg-meet-redHover text-white font-medium flex items-center gap-2 transition-all duration-200 shadow-lg ml-1"
        title="Leave call"
      >
        <PhoneOff :size="20" />
        <span class="hidden sm:inline text-sm font-semibold">Leave</span>
      </button>
    </div>

    <!-- Desktop Right Section: Side Panels & Host Controls -->
    <div class="hidden md:flex items-center justify-end gap-2 sm:gap-3 w-1/4">
      <!-- Host Controls (Shield) -->
      <button
        v-if="isHost"
        @click="meetingStore.togglePanel('host_controls')"
        class="relative p-2.5 rounded-full transition-colors"
        :class="
          meetingStore.activePanel === 'host_controls'
            ? 'bg-meet-primary text-gray-900'
            : 'hover:bg-meet-surfaceLight text-meet-text'
        "
        title="Host controls"
      >
        <ShieldAlert :size="20" />
      </button>

      <!-- Participant List Toggle -->
      <button
        @click="meetingStore.togglePanel('people')"
        class="relative p-2.5 rounded-full transition-colors"
        :class="
          meetingStore.activePanel === 'people'
            ? 'bg-meet-primary text-gray-900'
            : 'hover:bg-meet-surfaceLight text-meet-text'
        "
        title="Show everyone"
      >
        <Users :size="20" />
        <span
          v-if="meetingStore.waitingParticipants.length > 0 && isHost"
          class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-meet-yellow text-gray-900 text-[10px] font-bold flex items-center justify-center animate-bounce"
        >
          {{ meetingStore.waitingParticipants.length }}
        </span>
        <span
          v-else-if="participantCount > 0"
          class="absolute -top-1 -right-1 px-1 min-w-[16px] h-4 rounded-full bg-meet-surfaceLight text-meet-text text-[10px] font-semibold flex items-center justify-center"
        >
          {{ participantCount }}
        </span>
      </button>

      <!-- Chat Panel Toggle with Unread Badge -->
      <button
        @click="handleToggleChat"
        class="relative p-2.5 rounded-full transition-colors"
        :class="
          meetingStore.activePanel === 'chat'
            ? 'bg-meet-primary text-gray-900'
            : 'hover:bg-meet-surfaceLight text-meet-text'
        "
        title="Chat with everyone"
      >
        <MessageSquare :size="20" />
        <span
          v-if="chatStore.unreadCount > 0"
          class="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-meet-red text-white text-[11px] font-bold flex items-center justify-center shadow"
        >
          {{ chatStore.unreadCount }}
        </span>
      </button>
    </div>

    <!-- Mobile Actions Bottom Sheet Modal -->
    <div
      v-if="isMobileSheetOpen"
      class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex flex-col justify-end"
      @click.self="isMobileSheetOpen = false"
    >
      <div class="w-full bg-[#303134] rounded-t-3xl p-5 space-y-4 border-t border-meet-border shadow-2xl animate-in slide-in-from-bottom duration-200">
        <!-- Sheet Handle & Header -->
        <div class="flex items-center justify-between border-b border-white/10 pb-3">
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono bg-[#202124] px-2.5 py-1 rounded-md text-meet-primary">
              {{ meetingCode }}
            </span>
          </div>
          <button
            @click="isMobileSheetOpen = false"
            class="p-1 rounded-full text-meet-textMuted hover:text-white"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- Actions Grid -->
        <div class="grid grid-cols-3 gap-3 py-2">
          <!-- In-Call Messages -->
          <button
            @click="triggerMobilePanel('chat')"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors relative text-center"
          >
            <MessageSquare :size="22" class="text-meet-primary mb-1.5" />
            <span class="text-xs text-white font-medium">In-call chat</span>
            <span
              v-if="chatStore.unreadCount > 0"
              class="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-meet-red text-white text-[10px] font-bold"
            >
              {{ chatStore.unreadCount }}
            </span>
          </button>

          <!-- People / Participants -->
          <button
            @click="triggerMobilePanel('people')"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors relative text-center"
          >
            <Users :size="22" class="text-meet-green mb-1.5" />
            <span class="text-xs text-white font-medium">People ({{ participantCount }})</span>
            <span
              v-if="meetingStore.waitingParticipants.length > 0 && isHost"
              class="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-meet-yellow text-gray-900 text-[10px] font-bold animate-bounce"
            >
              {{ meetingStore.waitingParticipants.length }}
            </span>
          </button>

          <!-- Raise / Lower Hand -->
          <button
            @click="triggerMobileHand"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors text-center"
          >
            <Hand
              :size="22"
              :class="isHandRaised ? 'text-meet-yellow animate-bounce' : 'text-meet-yellow/80'"
              class="mb-1.5"
            />
            <span class="text-xs text-white font-medium">
              {{ isHandRaised ? 'Lower hand' : 'Raise hand' }}
            </span>
          </button>

          <!-- Screen Share -->
          <button
            @click="triggerMobileScreenShare"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors text-center"
          >
            <ScreenShare
              :size="22"
              :class="isScreenSharing ? 'text-meet-primary' : 'text-white/80'"
              class="mb-1.5"
            />
            <span class="text-xs text-white font-medium">
              {{ isScreenSharing ? 'Stop share' : 'Share screen' }}
            </span>
          </button>

          <!-- Host Controls (if host) -->
          <button
            v-if="isHost"
            @click="triggerMobilePanel('host_controls')"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors text-center"
          >
            <ShieldAlert :size="22" class="text-blue-400 mb-1.5" />
            <span class="text-xs text-white font-medium">Host controls</span>
          </button>

          <!-- Settings -->
          <button
            @click="triggerMobileDevices"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors text-center"
          >
            <Settings :size="22" class="text-gray-300 mb-1.5" />
            <span class="text-xs text-white font-medium">Settings</span>
          </button>

          <!-- Copy Link -->
          <button
            @click="copyCode"
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-[#202124] hover:bg-[#3c4043] transition-colors text-center"
          >
            <Copy :size="22" class="text-purple-400 mb-1.5" />
            <span class="text-xs text-white font-medium">{{ isCopied ? 'Copied!' : 'Copy info' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  ScreenShare,
  Hand,
  Settings,
  PhoneOff,
  Users,
  MessageSquare,
  ShieldAlert,
  MoreVertical,
  X,
  Copy,
} from 'lucide-vue-next'
import { useMeetingStore } from '@/stores/meeting'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  meetingCode: string
  isAudioEnabled: boolean
  isVideoEnabled: boolean
  isScreenSharing: boolean
  isHandRaised: boolean
  isHost: boolean
  participantCount: number
}>()

const emit = defineEmits([
  'toggle-mic',
  'toggle-camera',
  'toggle-screenshare',
  'toggle-hand',
  'open-devices',
  'leave',
])

const meetingStore = useMeetingStore()
const chatStore = useChatStore()

const currentTime = ref('')
const isMobileSheetOpen = ref(false)
const isCopied = ref(false)
let timer: number | null = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function handleToggleChat() {
  meetingStore.togglePanel('chat')
  if (meetingStore.activePanel === 'chat') {
    chatStore.openChat()
  } else {
    chatStore.closeChat()
  }
}

function triggerMobilePanel(panel: 'chat' | 'people' | 'host_controls') {
  isMobileSheetOpen.value = false
  meetingStore.togglePanel(panel)
  if (panel === 'chat') {
    chatStore.openChat()
  }
}

function triggerMobileHand() {
  isMobileSheetOpen.value = false
  emit('toggle-hand')
}

function triggerMobileScreenShare() {
  isMobileSheetOpen.value = false
  emit('toggle-screenshare')
}

function triggerMobileDevices() {
  isMobileSheetOpen.value = false
  emit('open-devices')
}

async function copyCode() {
  try {
    const url = `${window.location.origin}/meet/${props.meetingCode}`
    await navigator.clipboard.writeText(url)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (e) {
    console.warn('Copy error:', e)
  }
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
