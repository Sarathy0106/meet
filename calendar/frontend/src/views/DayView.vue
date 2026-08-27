<template>
  <div class="h-full w-full flex flex-col bg-white overflow-hidden select-none">
    <!-- Day Header -->
    <div class="border-b border-cal-border bg-gray-50/50 p-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-semibold text-gray-800">
          {{ formattedDayTitle }}
        </h3>
        <p class="text-xs text-gray-500">
          {{ dayEvents.length }} {{ dayEvents.length === 1 ? 'event' : 'events' }} scheduled
        </p>
      </div>
      <button
        @click="eventsStore.openCreateModal(eventsStore.currentDate)"
        class="px-4 py-1.5 bg-cal-blue hover:bg-cal-blueHover text-white text-xs font-semibold rounded-full shadow-xs"
      >
        + Add Event
      </button>
    </div>

    <!-- 24-hour Day Time Schedule -->
    <div ref="dayScroll" class="flex-1 overflow-y-auto relative">
      <div class="grid grid-cols-[64px_1fr] relative min-h-[1152px]">
        <!-- Hours Column -->
        <div class="border-r border-cal-border select-none">
          <div
            v-for="hour in 24"
            :key="hour"
            class="h-12 border-b border-transparent relative text-right pr-2"
          >
            <span class="text-xs text-gray-400 -top-2 relative block font-medium">
              {{ formatHourLabel(hour - 1) }}
            </span>
          </div>
        </div>

        <!-- Events Column -->
        <div class="relative">
          <!-- 24 Clickable Rows -->
          <div
            v-for="h in 24"
            :key="h"
            @click="handleSlotClick(h - 1)"
            class="h-12 border-b border-gray-100 hover:bg-blue-50/20 cursor-pointer transition-colors"
          ></div>

          <!-- Positioned Events -->
          <div
            v-for="ev in dayEvents"
            :key="ev.id"
            @click.stop="eventsStore.openDetailModal(ev)"
            class="absolute inset-x-2 rounded-xl p-3 text-white shadow-sm overflow-hidden cursor-pointer hover:brightness-95 transition-all z-10"
            :style="getEventStyle(ev)"
          >
            <div class="flex items-start justify-between">
              <div>
                <h4 class="font-bold text-xs leading-snug flex items-center gap-1.5">
                  <Video v-if="ev.meeting_link" :size="13" class="shrink-0" />
                  <span>{{ ev.title }}</span>
                </h4>
                <p class="text-[11px] opacity-90 mt-0.5">
                  {{ formatTime(ev.start_at) }} - {{ formatTime(ev.end_at) }}
                  <span v-if="ev.location"> · {{ ev.location }}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Video } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'
import type { CalendarEvent } from '@/types'

const eventsStore = useEventsStore()
const dayScroll = ref<HTMLDivElement | null>(null)

const formattedDayTitle = computed(() => {
  const d = eventsStore.currentDate
  return d.toLocaleDateString([], {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
})

const dayEvents = computed<CalendarEvent[]>(() => {
  const d = eventsStore.currentDate
  const y = d.getFullYear()
  const m = d.getMonth()
  const dateNum = d.getDate()

  return eventsStore.filteredEvents.filter((ev) => {
    const evStart = new Date(ev.start_at)
    return (
      evStart.getDate() === dateNum &&
      evStart.getMonth() === m &&
      evStart.getFullYear() === y
    )
  })
})

function formatHourLabel(h: number) {
  if (h === 0) return '12 AM'
  if (h < 12) return `${h} AM`
  if (h === 12) return '12 PM'
  return `${h - 12} PM`
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function getEventStyle(ev: CalendarEvent) {
  const start = new Date(ev.start_at)
  const end = new Date(ev.end_at)

  const startMinutes = start.getHours() * 60 + start.getMinutes()
  let durationMinutes = (end.getTime() - start.getTime()) / (1000 * 60)
  if (durationMinutes < 30) durationMinutes = 35

  const topPx = (startMinutes / 60) * 48
  const heightPx = (durationMinutes / 60) * 48

  return {
    top: `${topPx}px`,
    height: `${Math.max(28, heightPx)}px`,
    backgroundColor: ev.color || '#1a73e8',
  }
}

function handleSlotClick(hour: number) {
  const target = new Date(eventsStore.currentDate)
  target.setHours(hour, 0, 0, 0)
  eventsStore.openCreateModal(target)
}

onMounted(() => {
  if (dayScroll.value) {
    dayScroll.value.scrollTop = 8 * 48
  }
})
</script>
