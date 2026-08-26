<template>
  <div class="h-screen w-screen flex flex-col bg-[#202124] text-white overflow-hidden select-none">
    <!-- Reconnection Banner -->
    <div
      v-if="connectionStatus === 'reconnecting'"
      class="w-full bg-meet-yellow text-gray-950 py-1.5 px-4 text-xs font-semibold flex items-center justify-center gap-2 z-50 animate-pulse"
    >
      <span>⚠️ Reconnecting to meeting...</span>
    </div>

    <!-- Floating Notification Toasts -->
    <div class="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none">
      <transition-group
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="transform -translate-y-4 opacity-0"
        enter-to-class="transform translate-y-0 opacity-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-for="toast in toastNotifications"
          :key="toast.id"
          class="px-4 py-2 bg-[#303134] text-white text-xs font-medium rounded-full shadow-2xl border border-meet-border pointer-events-auto flex items-center gap-2"
        >
          <span>{{ toast.message }}</span>
        </div>
      </transition-group>
    </div>

    <!-- Main Workspace (Grid + Slide-over Drawer) -->
    <div class="flex-1 flex overflow-hidden relative">
      <!-- Video Tiles Stage -->
      <div class="flex-1 h-full min-w-0 flex flex-col relative overflow-hidden">
        <ParticipantGrid
          :local-participant="livekitManager.localParticipant"
          :remote-participants="remoteParticipants"
          :local-name="authStore.displayName"
          :active-speaker-identity="activeSpeakerIdentity"
        />
      </div>

      <!-- Right Drawer (Chat / People / Host Controls) -->
      <transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="translate-y-full md:translate-y-0 md:translate-x-full opacity-0 md:opacity-100"
        enter-to-class="translate-y-0 md:translate-x-0 opacity-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="translate-y-0 md:translate-x-0 opacity-100"
        leave-to-class="translate-y-full md:translate-y-0 md:translate-x-full opacity-0 md:opacity-100"
      >
        <div
          v-if="meetingStore.activePanel"
          class="fixed inset-0 md:relative md:inset-auto w-full md:w-96 h-full z-50 md:z-40 shrink-0 shadow-2xl bg-[#202124]"
        >
          <ChatPanel v-if="meetingStore.activePanel === 'chat'" />
          <ParticipantListPanel
            v-else-if="meetingStore.activePanel === 'people'"
            :local-name="authStore.displayName"
          />
          <HostControlsMenu
            v-else-if="meetingStore.activePanel === 'host_controls'"
            @end-for-all="handleLeave"
          />
        </div>
      </transition>
    </div>

    <!-- Bottom Control Bar -->
    <ControlBar
      :meeting-code="meetingCode"
      :is-audio-enabled="deviceStore.isAudioEnabled"
      :is-video-enabled="deviceStore.isVideoEnabled"
      :is-screen-sharing="deviceStore.isScreenSharing"
      :is-hand-raised="isLocalHandRaised"
      :is-host="meetingStore.isHost"
      :participant-count="totalParticipantsCount"
      @toggle-mic="toggleMic"
      @toggle-camera="toggleCamera"
      @toggle-screenshare="toggleScreenShare"
      @toggle-hand="toggleHandRaise"
      @open-devices="isDeviceModalOpen = true"
      @leave="handleLeave"
    />

    <!-- Device Settings Modal -->
    <DevicePickerModal
      :is-open="isDeviceModalOpen"
      @close="isDeviceModalOpen = false"
      @device-changed="applyDeviceChanges"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { RemoteParticipant } from 'livekit-client'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/devices'
import { useMeetingStore } from '@/stores/meeting'
import { useChatStore } from '@/stores/chat'
import { livekitManager } from '@/lib/livekit'
import { api } from '@/lib/api'
import ParticipantGrid from '@/components/call/ParticipantGrid.vue'
import ControlBar from '@/components/call/ControlBar.vue'
import ChatPanel from '@/components/call/ChatPanel.vue'
import ParticipantListPanel from '@/components/call/ParticipantListPanel.vue'
import HostControlsMenu from '@/components/call/HostControlsMenu.vue'
import DevicePickerModal from '@/components/call/DevicePickerModal.vue'
import type { DataPacket } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const meetingStore = useMeetingStore()
const chatStore = useChatStore()

const meetingCode = computed(() => (route.params.code as string).toLowerCase().trim())
const remoteParticipants = ref<RemoteParticipant[]>([])
const activeSpeakerIdentity = ref<string | null>(null)
const connectionStatus = ref<'connecting' | 'connected' | 'reconnecting' | 'disconnected'>('connecting')
const isDeviceModalOpen = ref(false)

interface Toast {
  id: string
  message: string
}
const toastNotifications = ref<Toast[]>([])

function addToast(message: string) {
  const id = `toast_${Date.now()}_${Math.random()}`
  toastNotifications.value.push({ id, message })
  setTimeout(() => {
    toastNotifications.value = toastNotifications.value.filter((t) => t.id !== id)
  }, 4000)
}

const isLocalHandRaised = computed(() => {
  const localId = livekitManager.localParticipant?.identity || 'local'
  return meetingStore.raisedHands.has(localId)
})

const totalParticipantsCount = computed(() => {
  return 1 + remoteParticipants.value.length
})

let cleanups: (() => void)[] = []
let lobbyPollTimer: number | null = null

async function initCall() {
  try {
    // 1. Fetch meeting metadata
    await meetingStore.fetchMeeting(meetingCode.value)

    // 2. Get LiveKit Token
    let token = route.query.token as string
    let livekitUrl = import.meta.env.VITE_LIVEKIT_URL || 'wss://demo.livekit.cloud'

    if (!token) {
      const res = await api.post(`/meetings/${meetingCode.value}/token`, {
        display_name: authStore.displayName,
        is_host: meetingStore.isHost,
      })
      token = res.data.token
      livekitUrl = res.data.livekit_url
    }

    // 3. Connect to LiveKit Room
    await livekitManager.connect(livekitUrl, token)

    // 4. Publish initial audio and video tracks according to store states
    if (deviceStore.isVideoEnabled) {
      await livekitManager.setCameraEnabled(true)
    }
    if (deviceStore.isAudioEnabled) {
      await livekitManager.setMicrophoneEnabled(true)
    }

    // 5. Setup LiveKit Callbacks
    cleanups.push(
      livekitManager.onParticipantUpdate(() => {
        remoteParticipants.value = [...livekitManager.remoteParticipants]
        meetingStore.fetchParticipants(meetingCode.value)
      })
    )

    cleanups.push(
      livekitManager.onActiveSpeakersChange((speakers) => {
        if (speakers.length > 0) {
          activeSpeakerIdentity.value = speakers[0].identity
        } else {
          activeSpeakerIdentity.value = null
        }
      })
    )

    cleanups.push(
      livekitManager.onConnectionStatusChange((status) => {
        connectionStatus.value = status
        if (status === 'disconnected') {
          router.push(`/meet/${meetingCode.value}/post`)
        }
      })
    )

    cleanups.push(
      livekitManager.onDataReceived((packet: DataPacket) => {
        handleIncomingDataPacket(packet)
      })
    )

    // 6. Load Chat History
    await chatStore.loadHistory(meetingCode.value)

    // 7. Periodic participant / lobby poll for hosts
    if (meetingStore.isHost) {
      lobbyPollTimer = window.setInterval(() => {
        meetingStore.fetchParticipants(meetingCode.value)
      }, 3000)
    }

    remoteParticipants.value = [...livekitManager.remoteParticipants]
  } catch (err: any) {
    console.error('Failed to initialize meeting call:', err)
    alert(err.response?.data?.detail || 'Unable to connect to meeting room.')
    router.push('/')
  }
}

function handleIncomingDataPacket(packet: DataPacket) {
  const localId = livekitManager.localParticipant?.identity

  switch (packet.type) {
    case 'chat':
      if (packet.payload) {
        chatStore.addMessage({
          id: packet.payload.id || `msg_${Date.now()}`,
          meeting_id: meetingStore.currentMeeting?.id || '',
          sender_name: packet.senderName || 'Participant',
          content: packet.payload.content,
          sent_at: packet.payload.sent_at || new Date().toISOString(),
          is_local: false,
        })
        if (!chatStore.isChatOpen) {
          addToast(`💬 ${packet.senderName}: ${packet.payload.content.substring(0, 40)}`)
        }
      }
      break

    case 'raise_hand':
      if (packet.senderId) {
        meetingStore.setHandRaise(packet.senderId, true)
        addToast(`✋ ${packet.senderName || 'A participant'} raised their hand`)
      }
      break

    case 'lower_hand':
      if (packet.senderId) {
        meetingStore.setHandRaise(packet.senderId, false)
      }
      break

    case 'mute_participant':
      if (packet.targetId === localId || packet.targetId === '*') {
        if (deviceStore.isAudioEnabled) {
          deviceStore.toggleAudio()
          livekitManager.setMicrophoneEnabled(false)
          addToast('🔇 You were muted by the host')
        }
      }
      break

    case 'kick_participant':
      if (packet.targetId === localId) {
        alert('You were removed from the meeting by the host.')
        handleLeave()
      }
      break

    case 'meeting_ended':
      alert('The host has ended the meeting.')
      router.push(`/meet/${meetingCode.value}/post`)
      break
  }
}

async function toggleMic() {
  deviceStore.toggleAudio()
  await livekitManager.setMicrophoneEnabled(deviceStore.isAudioEnabled)
}

async function toggleCamera() {
  deviceStore.toggleVideo()
  await livekitManager.setCameraEnabled(deviceStore.isVideoEnabled)
}

async function toggleScreenShare() {
  try {
    const nextState = !deviceStore.isScreenSharing
    await livekitManager.setScreenShareEnabled(nextState)
    deviceStore.isScreenSharing = nextState
  } catch (err) {
    console.warn('Screen share error:', err)
    deviceStore.isScreenSharing = false
  }
}

async function toggleHandRaise() {
  const localId = livekitManager.localParticipant?.identity || 'local'
  const isRaised = meetingStore.raisedHands.has(localId)
  meetingStore.setHandRaise(localId, !isRaised)

  await livekitManager.sendData({
    type: !isRaised ? 'raise_hand' : 'lower_hand',
    senderId: localId,
    senderName: authStore.displayName,
  })
}

async function applyDeviceChanges() {
  // Re-enable tracks with new devices
  if (deviceStore.isVideoEnabled) {
    await livekitManager.setCameraEnabled(true)
  }
  if (deviceStore.isAudioEnabled) {
    await livekitManager.setMicrophoneEnabled(true)
  }
}

async function handleLeave() {
  await meetingStore.leaveMeeting(meetingCode.value)
  livekitManager.disconnect()
  router.push(`/meet/${meetingCode.value}/post`)
}

onMounted(() => {
  initCall()
})

onUnmounted(() => {
  cleanups.forEach((c) => c())
  if (lobbyPollTimer) clearInterval(lobbyPollTimer)
  livekitManager.disconnect()
})
</script>
