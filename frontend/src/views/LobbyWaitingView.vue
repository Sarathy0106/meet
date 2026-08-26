<template>
  <div class="min-h-screen w-full flex flex-col items-center justify-center bg-[#202124] text-white p-6 select-none">
    <div class="max-w-md w-full text-center space-y-8 bg-[#303134] border border-meet-border rounded-3xl p-8 shadow-2xl">
      <!-- Animated Pulsing Lobby Avatar -->
      <div class="relative flex items-center justify-center mx-auto">
        <div class="w-24 h-24 rounded-full bg-meet-blue/20 flex items-center justify-center animate-ping absolute"></div>
        <div class="w-20 h-20 rounded-full bg-meet-blue flex items-center justify-center text-white text-2xl font-bold shadow-lg relative z-10">
          <Clock :size="36" />
        </div>
      </div>

      <div class="space-y-3">
        <h1 class="text-2xl font-medium text-white">Asking to join...</h1>
        <p class="text-sm text-meet-textMuted leading-relaxed">
          You'll join the call when someone in the meeting lets you in.
        </p>
      </div>

      <div class="p-3 bg-[#202124] rounded-xl border border-meet-border text-xs text-meet-textMuted font-mono">
        Meeting code: <span class="text-white">{{ meetingCode }}</span>
      </div>

      <div class="pt-4 border-t border-meet-border">
        <button
          @click="cancelJoin"
          class="w-full py-3 bg-meet-surfaceLight hover:bg-meet-border text-white text-sm font-medium rounded-full transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Clock } from 'lucide-vue-next'
import { useMeetingStore } from '@/stores/meeting'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'

const route = useRoute()
const router = useRouter()
const meetingStore = useMeetingStore()
const authStore = useAuthStore()

const meetingCode = computed(() => (route.params.code as string).toLowerCase().trim())
let pollInterval: number | null = null

async function checkAdmissionStatus() {
  try {
    const res = await api.post(`/meetings/${meetingCode.value}/join`, {
      display_name: authStore.displayName,
    })

    if (res.data.status === 'admitted') {
      if (pollInterval) clearInterval(pollInterval)
      meetingStore.setMeeting(res.data.meeting, res.data.participant_id, res.data.role, 'admitted')
      router.push({
        name: 'room',
        params: { code: meetingCode.value },
        query: { token: res.data.livekit_token || '' },
      })
    } else if (res.data.status === 'rejected') {
      if (pollInterval) clearInterval(pollInterval)
      alert('You were denied entry to this meeting.')
      router.push('/')
    }
  } catch (err) {
    console.warn('Lobby polling error:', err)
  }
}

function cancelJoin() {
  if (pollInterval) clearInterval(pollInterval)
  router.push('/')
}

onMounted(() => {
  // Poll admission status every 2 seconds
  pollInterval = window.setInterval(checkAdmissionStatus, 2000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
