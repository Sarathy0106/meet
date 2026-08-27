<template>
  <div class="h-full w-full flex flex-col bg-white overflow-hidden select-none">
    <!-- Header with 7 Days -->
    <div class="grid grid-cols-[56px_repeat(7,1fr)] border-b border-cal-border bg-gray-50/50 text-center shrink-0">
      <!-- Empty corner for GMT time header -->
      <div class="py-2.5 text-[10px] text-gray-400 font-medium border-r border-cal-border">
        GMT+0
      </div>

      <!-- 7 Days header columns -->
      <div
        v-for="day in weekDays"
        :key="day.dateStr"
        class="py-2 flex flex-col items-center justify-center border-r border-cal-border last:border-r-0"
      >
        <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
          {{ day.dayName }}
        </span>
        <span
          class="text-sm font-semibold w-7 h-7 flex items-center justify-center rounded-full mt-0.5"
          :class="day.isToday ? 'bg-cal-blue text-white shadow-xs' : 'text-gray-800'"
        >
          {{ day.dayNum }}
        </span>
      </div>
    </div>

    <!-- Scrollable 24-hour time grid -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto relative">
      <div class="grid grid-cols-[56px_repeat(7,1fr)] relative min-h-[1152px]">
        <!-- Left Time Column (0:00 to 23:00) -->
        <div class="border-r border-cal-border select-none">
          <div
            v-for="hour in 24"
            :key="hour"
            class="h-12 border-b border-transparent relative text-right pr-2"
          >
            <span class="text-[10px] text-gray-400 -top-2 relative block font-medium">
              {{ formatHourLabel(hour - 1) }}
            </span>
          </div>
        </div>

        <!-- 7 Day Columns -->
        <div
          v-for="day in weekDays"
          :key="day.dateStr"
          class="border-r border-cal-border last:border-r-0 relative group"
        >
          <!-- 24 hourly clickable slot rows -->
          <div
            v-for="h in 24"
            :key="h"
            @click="handleSlotClick(day.date, h - 1)"
            class="h-12 border-b border-gray-100 hover:bg-blue-50/20 cursor-pointer transition-colors"
          ></div>

          <!-- Current Time Indicator (if day is today) -->
          <div
            v-if="day.isToday"
            class="absolute inset-x-0 border-t-2 border-red-500 z-20 pointer-events-none flex items-center"
            :style="{ top: `${currentTimeTop}px` }"
          >
            <span class="w-2.5 h-2.5 rounded-full bg-red-500 -ml-1"></span>
          </div>

          <!-- Positioned Events in this Day Column -->
          <div
            v-for="ev in getEventsForDay(day.date)"
            :key="ev.id"
            @click.stop="eventsStore.openDetailModal(ev)"
            class="absolute inset-x-1 rounded-lg px-2 py-1 text-white shadow-xs overflow-hidden cursor-pointer hover:brightness-95 transition-all z-10"
            :style="getEventStyle(ev)"
          >
            <div class="flex items-center gap-1 font-semibold text-[11px] leading-tight truncate">
              <Video v-if="ev.meeting_link" :size="11" class="shrink-0" />
              <span class="truncate">{{ ev.title }}</span>
            </div>
            <p class="text-[10px] opacity-90 truncate">
              {{ formatTime(ev.start_at) }} - {{ formatTime(ev.end_at) }}
            </p>
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
const scrollContainer = ref<HTMLDivElement | null>(null)

interface DayHeader {
  date: Date
  dateStr: string
  dayName: string
  dayNum: number
  isToday: boolean
}

const weekDays = computed<DayHeader[]>(() => {
  const current = new Date(eventsStore.currentDate)
  const currentDayOfWeek = current.getDay() // 0 = Sun

  const startOfWeek = new Date(current)
  startOfWeek.setDate(current.getDate() - currentDayOfWeek)

  const today = new Date()
  const days: DayHeader[] = []
  const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

  for (let i = 0; i < 7; i++) {
    const d = new Date(startOfWeek)
    d.setDate(startOfWeek.getDate() + i)

    days.push({
      date: d,
      dateStr: d.toISOString().split('T')[0],
      dayName: dayNames[i],
      dayNum: d.getDate(),
      isToday:
        d.getDate() === today.getDate() &&
        d.getMonth() === today.getMonth() &&
        d.getFullYear() === today.getFullYear(),
    })
  }

  return days
})

const currentTimeTop = computed(() => {
  const now = new Date()
  const minutes = now.getHours() * 60 + now.getMinutes()
  return (minutes / 60) * 48 // 48px per hour
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

function getEventsForDay(date: Date): CalendarEvent[] {
  const y = date.getFullYear()
  const m = date.getMonth()
  const d = date.getDate()

  return eventsStore.filteredEvents.filter((ev) => {
    const evStart = new Date(ev.start_at)
    return (
      evStart.getDate() === d &&
      evStart.getMonth() === m &&
      evStart.getFullYear() === y
    )
  })
}

function getEventStyle(ev: CalendarEvent) {
  const start = new Date(ev.start_at)
  const end = new Date(ev.end_at)

  const startMinutes = start.getHours() * 60 + start.getMinutes()
  let durationMinutes = (end.getTime() - start.getTime()) / (1000 * 60)
  if (durationMinutes < 25) durationMinutes = 30 // Minimum visible block

  const topPx = (startMinutes / 60) * 48
  const heightPx = (durationMinutes / 60) * 48

  return {
    top: `${topPx}px`,
    height: `${Math.max(22, heightPx)}px`,
    backgroundColor: ev.color || '#1a73e8',
  }
}

function handleSlotClick(day: Date, hour: number) {
  const target = new Date(day)
  target.setHours(hour, 0, 0, 0)
  eventsStore.openCreateModal(target)
}

onMounted(() => {
  // Scroll to 8:00 AM automatically
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 8 * 48
  }
})
</script>
