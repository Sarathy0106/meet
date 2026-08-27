<template>
  <div class="min-h-screen w-full flex flex-col bg-[#202124] text-white select-none">
    <!-- Header -->
    <header class="h-16 px-6 flex items-center justify-between border-b border-meet-border">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-meet-blue flex items-center justify-center text-white shadow">
          <Video :size="20" />
        </div>
        <div class="flex items-center gap-1">
          <span class="font-bold text-lg">sidaz</span>
          <span class="font-light text-lg text-meet-textMuted">meet</span>
        </div>
      </div>

      <div v-if="authStore.isAuthenticated" class="flex items-center gap-2">
        <AvatarInitials :name="authStore.displayName" size="sm" />
        <span class="text-xs text-meet-textMuted hidden sm:inline">{{ authStore.user?.email }}</span>
      </div>
      <div v-else class="text-xs text-meet-textMuted">
        Joining as Guest
      </div>
    </header>

    <!-- Main Section -->
    <main class="flex-1 flex items-center justify-center p-6">
      <div class="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <!-- Left: Camera Preview Tile -->
        <div class="lg:col-span-7 flex flex-col items-center">
          <div class="relative w-full aspect-video bg-[#3c4043] rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center border border-meet-border group">
            <!-- Video Track -->
            <video
              ref="previewVideoRef"
              autoplay
              playsinline
              muted
              class="w-full h-full object-cover scale-x-[-1]"
              :class="{ 'hidden': !deviceStore.isVideoEnabled }"
            ></video>

            <!-- Avatar Fallback when camera is off -->
            <div
              v-if="!deviceStore.isVideoEnabled"
              class="absolute inset-0 flex flex-col items-center justify-center bg-[#303134]"
            >
              <AvatarInitials :name="guestDisplayName || authStore.displayName" size="2xl" />
            </div>

            <!-- Permission Warning Banner on Preview -->
            <div
              v-if="deviceStore.micPermissionState === 'denied' || deviceStore.camPermissionState === 'denied'"
              class="absolute top-4 inset-x-4 z-30 p-2.5 bg-gray-900/90 backdrop-blur-md rounded-xl border border-yellow-500/40 text-xs text-yellow-200 flex items-center justify-between shadow-xl"
            >
              <div class="flex items-center gap-2">
                <AlertTriangle :size="16" class="text-yellow-400 shrink-0" />
                <span>
                  {{
                    deviceStore.micPermissionState === 'denied' && deviceStore.camPermissionState === 'denied'
                      ? 'Microphone and Camera are blocked'
                      : deviceStore.micPermissionState === 'denied'
                      ? 'Microphone is blocked'
                      : 'Camera is blocked'
                  }}
                </span>
              </div>
              <button
                @click="openPermissionGuide"
                class="px-2.5 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 rounded-lg font-medium text-[11px] transition-colors"
              >
                Unblock
              </button>
            </div>

            <!-- Audio Level Indicator (Visual sound wave meter) -->
            <div
              v-if="deviceStore.isAudioEnabled"
              class="absolute bottom-4 left-4 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-full border border-white/10"
              title="Microphone input level"
            >
              <Mic :size="14" class="text-meet-green" />
              <div class="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-meet-green transition-all duration-75"
                  :style="{ width: `${deviceStore.audioLevel}%` }"
                ></div>
              </div>
            </div>

            <!-- Bottom Video Overlay Controls (Mic & Cam toggle) -->
            <div class="absolute bottom-4 inset-x-0 flex items-center justify-center gap-3 z-20">
              <button
                @click="handleToggleMic"
                class="p-3.5 rounded-full transition-all duration-150 shadow-lg relative"
                :class="
                  deviceStore.isAudioEnabled
                    ? 'bg-meet-surface hover:bg-meet-surfaceLight text-white'
                    : 'bg-meet-red hover:bg-meet-redHover text-white'
                "
                :title="deviceStore.isAudioEnabled ? 'Turn off microphone' : 'Turn on microphone'"
              >
                <Mic v-if="deviceStore.isAudioEnabled" :size="20" />
                <MicOff v-else :size="20" />
              </button>

              <button
                @click="handleToggleCamera"
                class="p-3.5 rounded-full transition-all duration-150 shadow-lg"
                :class="
                  deviceStore.isVideoEnabled
                    ? 'bg-meet-surface hover:bg-meet-surfaceLight text-white'
                    : 'bg-meet-red hover:bg-meet-redHover text-white'
                "
                :title="deviceStore.isVideoEnabled ? 'Turn off camera' : 'Turn on camera'"
              >
                <Video v-if="deviceStore.isVideoEnabled" :size="20" />
                <VideoOff v-else :size="20" />
              </button>

              <button
                @click="isDeviceModalOpen = true"
                class="p-3.5 rounded-full bg-meet-surface hover:bg-meet-surfaceLight text-white transition-colors shadow-lg"
                title="Device Settings"
              >
                <Settings :size="20" />
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Join Actions & Info -->
        <div class="lg:col-span-5 space-y-6 flex flex-col justify-center">
          <div class="space-y-2">
            <h1 class="text-3xl font-medium text-white">Ready to join?</h1>
            <p class="text-sm text-meet-textMuted">
              {{ participantStatusText }}
            </p>
          </div>

          <!-- Permission Status Hint if blocked -->
          <div
            v-if="deviceStore.micPermissionState === 'denied' || deviceStore.camPermissionState === 'denied'"
            class="p-3.5 bg-[#303134] border border-meet-border rounded-xl space-y-2"
          >
            <div class="flex items-center gap-2 text-xs font-semibold text-white">
              <ShieldAlert :size="16" class="text-yellow-400" />
              <span>Permission Notice</span>
            </div>
            <p class="text-xs text-meet-textMuted">
              You can still join the call without permissions and unmute or turn on video anytime later.
            </p>
            <button
              @click="openPermissionGuide"
              class="text-xs text-meet-blue hover:underline font-medium inline-flex items-center gap-1"
            >
              <span>How to allow microphone & camera</span>
              <ExternalLink :size="12" />
            </button>
          </div>

          <!-- Guest Name Input (if not logged in) -->
          <div v-if="!authStore.isAuthenticated" class="space-y-1.5">
            <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
              Your Name
            </label>
            <input
              v-model="guestDisplayName"
              type="text"
              required
              placeholder="What's your name?"
              class="w-full px-4 py-3 bg-[#303134] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
            />
          </div>

          <!-- Error Alert -->
          <div v-if="errorMessage" class="p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-300 text-xs">
            {{ errorMessage }}
          </div>

          <!-- Action Buttons -->
          <div class="space-y-3">
            <button
              @click="handleJoin"
              :disabled="isLoading || (!authStore.isAuthenticated && !guestDisplayName.trim())"
              class="w-full py-3.5 px-6 bg-meet-blue hover:bg-meet-blue-hover disabled:opacity-40 text-white rounded-full font-medium text-sm flex items-center justify-center gap-2 shadow-lg transition-all"
            >
              <span v-if="isLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              <span>{{ joinButtonLabel }}</span>
            </button>

            <button
              @click="router.push('/')"
              class="w-full py-2 text-xs text-meet-textMuted hover:text-white transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Device Settings Modal -->
    <DevicePickerModal
      :is-open="isDeviceModalOpen"
      @close="isDeviceModalOpen = false"
      @device-changed="deviceStore.startPreviewStream()"
    />

    <!-- Permission Guide Modal -->
    <PermissionGuideModal
      :is-open="deviceStore.isPermissionGuideOpen"
      :kind="deviceStore.activePermissionGuideKind"
      @close="deviceStore.closePermissionGuide()"
      @retry-success="setupPreview"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Video, VideoOff, Mic, MicOff, Settings, AlertTriangle, ShieldAlert, ExternalLink } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/devices'
import { useMeetingStore } from '@/stores/meeting'
import { api } from '@/lib/api'
import AvatarInitials from '@/components/common/AvatarInitials.vue'
import DevicePickerModal from '@/components/call/DevicePickerModal.vue'
import PermissionGuideModal from '@/components/common/PermissionGuideModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const meetingStore = useMeetingStore()

const meetingCode = computed(() => (route.params.code as string).toLowerCase().trim())
const previewVideoRef = ref<HTMLVideoElement | null>(null)
const isDeviceModalOpen = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const guestDisplayName = ref(authStore.guestName || '')

const isHost = computed(() => {
  if (!authStore.user || !meetingStore.currentMeeting) return false
  return meetingStore.currentMeeting.host_id === authStore.user.id
})

const joinButtonLabel = computed(() => {
  if (meetingStore.currentMeeting?.lobby_enabled && !isHost.value) {
    return 'Ask to join'
  }
  return 'Join now'
})

const participantStatusText = computed(() => {
  const count = meetingStore.currentMeeting?.active_participants_count || 0
  if (count === 0) return 'No one else is here'
  if (count === 1) return '1 person is in this call'
  return `${count} people are in this call`
})

async function fetchMeetingMetadata() {
  try {
    const res = await meetingStore.fetchMeeting(meetingCode.value)
    if (res.ended_at) {
      errorMessage.value = 'This meeting has already ended.'
    } else if (res.is_locked && !isHost.value) {
      errorMessage.value = 'This meeting is locked by the host.'
    }
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Meeting not found.'
  }
}

async function setupPreview() {
  await deviceStore.startPreviewStream()
  if (previewVideoRef.value && deviceStore.localPreviewStream) {
    previewVideoRef.value.srcObject = deviceStore.localPreviewStream
  }
}

async function handleToggleMic() {
  try {
    await deviceStore.toggleAudio()
  } catch {
    if (deviceStore.micPermissionState === 'denied') {
      deviceStore.openPermissionGuide('microphone')
    }
  }
}

async function handleToggleCamera() {
  try {
    await deviceStore.toggleVideo()
    if (previewVideoRef.value && deviceStore.localPreviewStream) {
      previewVideoRef.value.srcObject = deviceStore.localPreviewStream
    }
  } catch {
    if (deviceStore.camPermissionState === 'denied') {
      deviceStore.openPermissionGuide('camera')
    }
  }
}

function openPermissionGuide() {
  const kind =
    deviceStore.micPermissionState === 'denied' && deviceStore.camPermissionState === 'denied'
      ? 'both'
      : deviceStore.micPermissionState === 'denied'
      ? 'microphone'
      : 'camera'
  deviceStore.openPermissionGuide(kind)
}

async function handleJoin() {
  if (!authStore.isAuthenticated && guestDisplayName.value.trim()) {
    authStore.setGuestName(guestDisplayName.value.trim())
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const res = await api.post(`/meetings/${meetingCode.value}/join`, {
      display_name: guestDisplayName.value.trim() || authStore.displayName,
    })

    meetingStore.setMeeting(
      res.data.meeting,
      res.data.participant_id,
      res.data.role,
      res.data.status
    )

    if (res.data.status === 'waiting') {
      router.push(`/meet/${meetingCode.value}/waiting`)
    } else {
      router.push({
        name: 'room',
        params: { code: meetingCode.value },
        query: { token: res.data.livekit_token || '' },
      })
    }
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to join meeting.'
  } finally {
    isLoading.value = false
  }
}

watch(
  () => deviceStore.localPreviewStream,
  (stream) => {
    if (previewVideoRef.value && stream) {
      previewVideoRef.value.srcObject = stream
    }
  }
)

onMounted(async () => {
  await fetchMeetingMetadata()
  await setupPreview()
})

onUnmounted(() => {
  deviceStore.stopPreviewStream()
})
</script>
