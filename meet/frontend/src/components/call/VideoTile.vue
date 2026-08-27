<template>
  <div
    class="video-tile-container group relative w-full h-full flex items-center justify-center bg-[#3c4043] rounded-xl overflow-hidden select-none transition-all duration-200"
    :class="{
      'outline outline-2 outline-meet-primary shadow-lg shadow-blue-500/10': isActiveSpeaker,
      'border border-yellow-400/50': isHandRaised,
    }"
  >
    <!-- Video Element -->
    <video
      ref="videoRef"
      autoplay
      playsinline
      :muted="isLocal"
      class="w-full h-full object-cover"
      :class="{
        'scale-x-[-1]': isLocal && !isScreenShare,
        'hidden': !isVideoTrackActive,
      }"
    ></video>

    <!-- Audio Element (for remote participants) -->
    <audio
      v-if="!isLocal"
      ref="audioRef"
      autoplay
    ></audio>

    <!-- Avatar Placeholder when video is off -->
    <div
      v-if="!isVideoTrackActive"
      class="absolute inset-0 flex flex-col items-center justify-center bg-[#3c4043] z-10"
    >
      <AvatarInitials :name="displayName" size="xl" />
    </div>

    <!-- Hand Raised Badge -->
    <div
      v-if="isHandRaised"
      class="absolute top-3 left-3 z-20 flex items-center gap-1.5 px-2.5 py-1 bg-meet-yellow text-gray-900 rounded-full font-medium text-xs shadow-md animate-bounce"
    >
      <span>✋</span>
      <span>Raised Hand</span>
    </div>

    <!-- Top Right Overlay Controls (Pin, Connection quality) -->
    <div
      class="absolute top-3 right-3 z-20 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
    >
      <button
        @click.stop="$emit('toggle-pin')"
        class="p-1.5 rounded-full bg-black/60 hover:bg-black/80 text-white backdrop-blur-sm transition-colors"
        :title="isPinned ? 'Unpin' : 'Pin to main screen'"
      >
        <Pin :size="14" :class="{ 'text-meet-primary fill-meet-primary': isPinned }" />
      </button>
      <ConnectionQualityBadge :quality="connectionQuality" />
    </div>

    <!-- Bottom Left Tag (Display Name, Role, Screen share tag) -->
    <div
      class="absolute bottom-3 left-3 z-20 flex items-center gap-2 max-w-[85%] px-2.5 py-1 bg-black/60 backdrop-blur-md rounded-md text-white text-xs font-medium truncate"
    >
      <span class="truncate">{{ displayName }} {{ isLocal ? '(You)' : '' }}</span>
      <span v-if="isScreenShare" class="text-meet-primary font-normal">(Presentation)</span>
      <span
        v-if="role === 'host'"
        class="px-1.5 py-0.2 bg-blue-500/30 text-blue-300 rounded text-[10px] uppercase font-semibold tracking-wider"
      >
        Host
      </span>
    </div>

    <!-- Bottom Right Mic Status -->
    <div class="absolute bottom-3 right-3 z-20 flex items-center">
      <div
        v-if="!isAudioTrackActive"
        class="p-1.5 rounded-full bg-meet-red text-white shadow"
        title="Microphone is off"
      >
        <MicOff :size="13" />
      </div>
      <div
        v-else-if="isActiveSpeaker"
        class="p-1.5 rounded-full bg-meet-green text-white shadow"
        title="Speaking"
      >
        <Volume2 :size="13" class="animate-pulse" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import {
  Track,
  Participant as LKParticipant,
  RemoteParticipant,
} from 'livekit-client'
import { Pin, MicOff, Volume2 } from 'lucide-vue-next'
import AvatarInitials from '@/components/common/AvatarInitials.vue'
import ConnectionQualityBadge from '@/components/common/ConnectionQualityBadge.vue'

const props = withDefaults(
  defineProps<{
    participant?: LKParticipant | null
    customDisplayName?: string
    isLocal?: boolean
    isScreenShare?: boolean
    customStream?: MediaStream | null
    isAudioMuted?: boolean
    isVideoMuted?: boolean
    isActiveSpeaker?: boolean
    isHandRaised?: boolean
    isPinned?: boolean
    role?: 'host' | 'co_host' | 'participant'
  }>(),
  {
    participant: null,
    customDisplayName: '',
    isLocal: false,
    isScreenShare: false,
    customStream: null,
    isAudioMuted: false,
    isVideoMuted: false,
    isActiveSpeaker: false,
    isHandRaised: false,
    isPinned: false,
    role: 'participant',
  }
)

defineEmits(['toggle-pin'])

const videoRef = ref<HTMLVideoElement | null>(null)
const audioRef = ref<HTMLAudioElement | null>(null)

const displayName = computed(() => {
  if (props.customDisplayName) return props.customDisplayName
  if (props.participant?.name) return props.participant.name
  if (props.participant?.identity) return props.participant.identity
  return props.isLocal ? 'You' : 'Participant'
})

const isVideoTrackActive = computed(() => {
  if (props.customStream) {
    const videoTracks = props.customStream.getVideoTracks()
    return videoTracks.length > 0 && videoTracks[0].enabled
  }
  if (props.participant) {
    if (props.isScreenShare) {
      return props.participant.isScreenShareEnabled
    }
    return props.participant.isCameraEnabled && !props.isVideoMuted
  }
  return !props.isVideoMuted
})

const isAudioTrackActive = computed(() => {
  if (props.customStream) {
    const audioTracks = props.customStream.getAudioTracks()
    return audioTracks.length > 0 && audioTracks[0].enabled
  }
  if (props.participant) {
    return props.participant.isMicrophoneEnabled && !props.isAudioMuted
  }
  return !props.isAudioMuted
})

const connectionQuality = computed(() => {
  if (!props.participant) return 'good'
  const q = props.participant.connectionQuality
  if (q === 'excellent') return 'excellent'
  if (q === 'good') return 'good'
  if (q === 'poor') return 'poor'
  return 'good'
})

function attachTracks() {
  if (props.customStream && videoRef.value) {
    videoRef.value.srcObject = props.customStream
    return
  }

  if (!props.participant) return

  // Attach video
  if (videoRef.value) {
    const publication = props.isScreenShare
      ? props.participant.getTrackPublication(Track.Source.ScreenShare)
      : props.participant.getTrackPublication(Track.Source.Camera)

    if (publication && publication.track) {
      publication.track.attach(videoRef.value)
    }
  }

  // Attach remote audio
  if (!props.isLocal && audioRef.value && props.participant instanceof RemoteParticipant) {
    const audioPublication = props.participant.getTrackPublication(Track.Source.Microphone)
    if (audioPublication && audioPublication.track) {
      audioPublication.track.attach(audioRef.value)
    }
  }
}

function detachTracks() {
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject = null
  }
}

watch(
  () => [props.participant, props.customStream, props.isScreenShare],
  () => {
    attachTracks()
  },
  { deep: true }
)

onMounted(() => {
  attachTracks()
})

onUnmounted(() => {
  detachTracks()
})
</script>
