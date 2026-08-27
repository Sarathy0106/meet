<template>
  <div class="min-h-screen w-full bg-gray-50 flex items-center justify-center p-4 select-none">
    <div class="max-w-md w-full bg-white border border-gray-200 rounded-3xl shadow-xl p-8 space-y-6 text-center">
      <!-- Brand Logo -->
      <div class="flex items-center justify-center gap-2">
        <div class="w-10 h-10 rounded-2xl bg-cal-blue text-white font-bold flex items-center justify-center shadow">
          M
        </div>
        <span class="text-lg font-bold text-gray-900">Meridian Calendar</span>
      </div>

      <div v-if="isLoading" class="py-12 space-y-3">
        <div class="w-8 h-8 border-3 border-cal-blue border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p class="text-xs text-gray-500">Processing your RSVP response...</p>
      </div>

      <div v-else-if="rsvpInfo" class="space-y-5">
        <!-- Status Icon / Feedback -->
        <div class="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl">
          <CheckCircle2 :size="32" class="text-emerald-500 mx-auto mb-1" />
          <h2 class="text-base font-bold text-emerald-900">RSVP Confirmed</h2>
          <p class="text-xs text-emerald-700 mt-0.5">
            Your response: <strong class="uppercase">{{ currentStatus }}</strong>
          </p>
        </div>

        <!-- Event Summary Card -->
        <div class="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-left space-y-2.5">
          <h3 class="text-base font-bold text-gray-900 leading-snug">
            {{ rsvpInfo.event_title }}
          </h3>
          <p class="text-xs text-gray-600 flex items-center gap-1.5">
            <Clock :size="14" class="text-gray-400 shrink-0" />
            <span>{{ formattedTime }}</span>
          </p>

          <div v-if="rsvpInfo.meeting_link" class="pt-2 border-t border-gray-200">
            <a
              :href="rsvpInfo.meeting_link"
              target="_blank"
              class="inline-flex items-center gap-1.5 text-xs font-semibold text-cal-blue hover:underline"
            >
              <Video :size="14" />
              <span>Join with Sidaz Meet</span>
            </a>
          </div>
        </div>

        <!-- Change Response Buttons -->
        <div class="space-y-2">
          <p class="text-xs text-gray-500 font-medium">Change your answer:</p>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="st in (['yes', 'maybe', 'no'] as const)"
              :key="st"
              @click="handleUpdateRsvp(st)"
              class="py-2 rounded-xl text-xs font-medium capitalize border transition-all"
              :class="
                currentStatus === st
                  ? 'bg-cal-blue text-white border-cal-blue shadow-sm font-semibold'
                  : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
              "
            >
              {{ st }}
            </button>
          </div>
        </div>

        <!-- Download ICS -->
        <div class="pt-4 border-t border-gray-100">
          <button
            @click="downloadICS"
            class="w-full py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
          >
            <Download :size="14" />
            <span>Download .ics Calendar File</span>
          </button>
        </div>
      </div>

      <div v-else class="py-8 space-y-3">
        <AlertCircle :size="36" class="text-red-500 mx-auto" />
        <h3 class="text-sm font-bold text-gray-800">Invalid or Expired Link</h3>
        <p class="text-xs text-gray-500">This RSVP link is no longer valid.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle2, Clock, Video, Download, AlertCircle } from 'lucide-vue-next'
import { api } from '@/lib/api'

const route = useRoute()
const token = computed(() => route.params.token as string)
const initialStatus = computed(() => route.query.status as string)

const isLoading = ref(true)
const rsvpInfo = ref<any>(null)
const currentStatus = ref('yes')

const formattedTime = computed(() => {
  if (!rsvpInfo.value?.start_at) return ''
  const start = new Date(rsvpInfo.value.start_at)
  const end = new Date(rsvpInfo.value.end_at)
  return `${start.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })} · ${start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
})

async function fetchRsvp() {
  isLoading.value = true
  try {
    const res = await api.get(`/rsvp/${token.value}`)
    rsvpInfo.value = res.data
    currentStatus.value = rsvpInfo.value.current_rsvp_status || 'yes'

    // If a status was in the query parameter (e.g. ?status=yes from 1-click email button), submit it
    if (initialStatus.value && ['yes', 'no', 'maybe'].includes(initialStatus.value)) {
      await handleUpdateRsvp(initialStatus.value as any)
    }
  } catch (e) {
    console.warn('Failed to load RSVP info:', e)
  } finally {
    isLoading.value = false
  }
}

async function handleUpdateRsvp(status: 'yes' | 'maybe' | 'no') {
  try {
    const res = await api.post(`/rsvp/${token.value}?status=${status}`)
    currentStatus.value = res.data.status
  } catch (e) {
    console.warn('Failed to update RSVP:', e)
  }
}

function downloadICS() {
  if (!rsvpInfo.value?.event_id) return
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  window.open(`${baseUrl}/events/${rsvpInfo.value.event_id}/ics`, '_blank')
}

onMounted(() => {
  fetchRsvp()
})
</script>
