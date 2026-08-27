<template>
  <div
    v-if="eventsStore.isDetailModalOpen && event"
    class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    @click.self="eventsStore.closeDetailModal()"
  >
    <div class="w-full max-w-lg bg-white border border-cal-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header Actions (Delete, ICS Download, Close) -->
      <div class="px-6 py-3.5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
        <div class="flex items-center gap-1.5">
          <span
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: event.color || '#1a73e8' }"
          ></span>
          <span class="text-xs text-gray-500 font-medium capitalize">{{ event.source }} Event</span>
        </div>

        <div class="flex items-center gap-1">
          <!-- Download ICS Button -->
          <button
            @click="eventsStore.downloadICS(event.id)"
            class="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
            title="Download .ics file"
          >
            <Download :size="16" />
          </button>

          <!-- Resend Invites Button (if attendees exist) -->
          <button
            v-if="event.attendees && event.attendees.length > 0"
            @click="handleResendInvites"
            :disabled="isInviting"
            class="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
            title="Resend email invitations"
          >
            <Mail :size="16" />
          </button>

          <!-- Delete Event Button -->
          <button
            @click="handleDelete"
            class="p-2 rounded-full hover:bg-red-50 text-gray-600 hover:text-red-600 transition-colors"
            title="Delete event"
          >
            <Trash2 :size="16" />
          </button>

          <!-- Close -->
          <button
            @click="eventsStore.closeDetailModal()"
            class="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <X :size="16" />
          </button>
        </div>
      </div>

      <!-- Detail Body -->
      <div class="p-6 overflow-y-auto space-y-5">
        <!-- Title & Date -->
        <div>
          <h2 class="text-xl font-bold text-gray-900 leading-tight">
            {{ event.title }}
          </h2>
          <p class="text-xs text-gray-600 mt-1 font-medium flex items-center gap-1.5">
            <Clock :size="13" class="text-gray-400" />
            <span>{{ formattedDateRange }}</span>
          </p>
        </div>

        <!-- Join with Sidaz Meet Call-to-Action -->
        <div
          v-if="event.meeting_link"
          class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50/50 border border-blue-200/80 rounded-2xl space-y-3 shadow-sm"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <div class="p-2 rounded-xl bg-cal-blue text-white shadow">
                <Video :size="18" />
              </div>
              <div>
                <p class="text-xs font-bold text-gray-900">Sidaz Meet</p>
                <p class="text-[11px] text-gray-500 font-mono">{{ event.meeting_link }}</p>
              </div>
            </div>
          </div>

          <a
            :href="event.meeting_link"
            target="_blank"
            class="w-full py-2.5 px-4 bg-cal-blue hover:bg-cal-blueHover text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow transition-all active:scale-[0.99]"
          >
            <span>Join with Sidaz Meet</span>
            <ExternalLink :size="13" />
          </a>
        </div>

        <!-- Location -->
        <div v-if="event.location" class="flex items-start gap-3 text-xs text-gray-700">
          <MapPin :size="16" class="text-gray-400 shrink-0 mt-0.5" />
          <span>{{ event.location }}</span>
        </div>

        <!-- Description -->
        <div v-if="event.description" class="flex items-start gap-3 text-xs text-gray-700">
          <AlignLeft :size="16" class="text-gray-400 shrink-0 mt-0.5" />
          <div class="whitespace-pre-wrap leading-relaxed">{{ event.description }}</div>
        </div>

        <!-- Attendees List -->
        <div v-if="event.attendees && event.attendees.length > 0" class="space-y-2.5 pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between text-xs font-semibold text-gray-700">
            <div class="flex items-center gap-1.5">
              <Users :size="14" class="text-cal-blue" />
              <span>Guests & Attendees ({{ event.attendees.length }})</span>
            </div>
            <span class="text-[11px] text-gray-400">
              {{ acceptedCount }} yes, {{ pendingCount }} pending
            </span>
          </div>

          <div class="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            <div
              v-for="att in event.attendees"
              :key="att.email"
              class="flex items-center justify-between py-1 px-2 rounded-lg bg-gray-50 text-xs"
            >
              <div class="flex items-center gap-2 truncate">
                <span class="w-5 h-5 rounded-full bg-gray-200 text-gray-700 text-[10px] font-bold flex items-center justify-center shrink-0">
                  {{ att.email.slice(0, 1).toUpperCase() }}
                </span>
                <span class="truncate text-gray-800">{{ att.email }}</span>
              </div>

              <!-- Status Badge -->
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider shrink-0"
                :class="
                  att.rsvp_status === 'yes'
                    ? 'bg-emerald-100 text-emerald-800'
                    : att.rsvp_status === 'no'
                    ? 'bg-red-100 text-red-800'
                    : att.rsvp_status === 'maybe'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-200 text-gray-600'
                "
              >
                {{ att.rsvp_status }}
              </span>
            </div>
          </div>
        </div>

        <!-- RSVP User Quick Response -->
        <div class="pt-3 border-t border-gray-100 flex items-center justify-between">
          <span class="text-xs font-semibold text-gray-700">Going?</span>
          <div class="flex items-center gap-1.5">
            <button
              v-for="st in (['yes', 'maybe', 'no'] as const)"
              :key="st"
              @click="handleRsvp(st)"
              class="px-3 py-1.5 rounded-lg text-xs font-medium capitalize border transition-all"
              :class="
                userRsvpStatus === st
                  ? 'bg-cal-blue text-white border-cal-blue shadow-sm font-semibold'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              "
            >
              {{ st }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Clock, Video, Users, MapPin, AlignLeft, Trash2, Download, Mail, ExternalLink } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'
import { useAuthStore } from '@/stores/auth'

const eventsStore = useEventsStore()
const authStore = useAuthStore()
const isInviting = ref(false)

const event = computed(() => eventsStore.selectedEvent)

const userRsvpStatus = computed(() => {
  if (!event.value || !authStore.user) return null
  const att = event.value.attendees?.find(
    (a) => a.email.toLowerCase() === authStore.user?.email.toLowerCase()
  )
  return att?.rsvp_status || null
})

const acceptedCount = computed(() => {
  return event.value?.attendees?.filter((a) => a.rsvp_status === 'yes').length || 0
})

const pendingCount = computed(() => {
  return event.value?.attendees?.filter((a) => a.rsvp_status === 'pending').length || 0
})

const formattedDateRange = computed(() => {
  if (!event.value) return ''
  const start = new Date(event.value.start_at)
  const end = new Date(event.value.end_at)

  const dateStr = start.toLocaleDateString([], {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  if (event.value.all_day) {
    return `${dateStr} (All day)`
  }

  const startTime = start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const endTime = end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return `${dateStr} · ${startTime} - ${endTime}`
})

async function handleRsvp(status: 'yes' | 'maybe' | 'no') {
  if (!event.value) return
  await eventsStore.rsvpEvent(event.value.id, status)
}

async function handleResendInvites() {
  if (!event.value) return
  isInviting.value = true
  try {
    await eventsStore.resendInvites(event.value.id)
    alert('Email invitations with .ics files sent to attendees!')
  } catch (e) {
    alert('Failed to send invitations.')
  } finally {
    isInviting.value = false
  }
}

async function handleDelete() {
  if (!event.value) return
  if (confirm(`Delete "${event.value.title}"?`)) {
    await eventsStore.deleteEvent(event.value.id)
  }
}
</script>
