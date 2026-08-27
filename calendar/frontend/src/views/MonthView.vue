<template>
  <div class="h-full w-full flex flex-col bg-white overflow-hidden select-none">
    <!-- Days of Week Header -->
    <div class="grid grid-cols-7 border-b border-cal-border bg-gray-50/50 text-center py-2 text-xs font-semibold text-gray-600">
      <div v-for="day in weekDays" :key="day" class="tracking-wide">
        {{ day }}
      </div>
    </div>

    <!-- Month Matrix Grid -->
    <div class="flex-1 grid grid-cols-7 grid-rows-5 lg:grid-rows-5 divide-x divide-y divide-cal-border overflow-y-auto">
      <div
        v-for="cell in matrixCells"
        :key="cell.dateStr"
        @click="handleCellClick(cell.date)"
        class="min-h-[90px] p-1.5 flex flex-col transition-colors group cursor-pointer hover:bg-blue-50/20"
        :class="{
          'bg-gray-50/40 text-gray-400': !cell.isCurrentMonth,
          'bg-white text-gray-800': cell.isCurrentMonth,
        }"
      >
        <!-- Cell Date Number & Today Indicator -->
        <div class="flex items-center justify-between mb-1">
          <span
            class="text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full transition-colors"
            :class="
              cell.isToday
                ? 'bg-cal-blue text-white font-bold shadow-xs'
                : 'group-hover:bg-gray-200'
            "
          >
            {{ cell.dayNumber }}
          </span>
        </div>

        <!-- Event Chips -->
        <div class="flex-1 space-y-1 overflow-hidden">
          <div
            v-for="ev in cell.events.slice(0, 3)"
            :key="ev.id"
            @click.stop="eventsStore.openDetailModal(ev)"
            class="px-2 py-0.5 rounded text-[11px] font-medium truncate flex items-center gap-1 shadow-2xs hover:opacity-90 transition-opacity cursor-pointer text-white"
            :style="{ backgroundColor: ev.color || '#1a73e8' }"
            :title="ev.title"
          >
            <Video v-if="ev.meeting_link" :size="11" class="shrink-0" />
            <span v-if="!ev.all_day" class="text-[10px] opacity-90 shrink-0 font-normal">
              {{ formatEventTime(ev.start_at) }}
            </span>
            <span class="truncate">{{ ev.title }}</span>
          </div>

          <!-- Overflow (+N more) -->
          <div
            v-if="cell.events.length > 3"
            class="text-[10px] text-gray-500 font-semibold px-1 hover:text-cal-blue cursor-pointer"
          >
            +{{ cell.events.length - 3 }} more
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Video } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'
import type { CalendarEvent } from '@/types'

const eventsStore = useEventsStore()
const weekDays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

interface MonthCell {
  date: Date
  dateStr: string
  dayNumber: number
  isCurrentMonth: boolean
  isToday: boolean
  events: CalendarEvent[]
}

function formatEventTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

const matrixCells = computed<MonthCell[]>(() => {
  const current = eventsStore.currentDate
  const year = current.getFullYear()
  const month = current.getMonth()

  const firstDay = new Date(year, month, 1)
  const startDayOfWeek = firstDay.getDay() // 0 = Sun

  const today = new Date()
  const cells: MonthCell[] = []

  // Preceding month days
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    const d = new Date(year, month, -i)
    cells.push(buildCell(d, false, today))
  }

  // Current month days
  const totalDays = new Date(year, month + 1, 0).getDate()
  for (let i = 1; i <= totalDays; i++) {
    const d = new Date(year, month, i)
    cells.push(buildCell(d, true, today))
  }

  // Trailing next month days to reach 35
  const remaining = 35 - cells.length
  if (remaining > 0) {
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i)
      cells.push(buildCell(d, false, today))
    }
  }

  return cells
})

function buildCell(date: Date, isCurrentMonth: boolean, today: Date): MonthCell {
  const y = date.getFullYear()
  const m = date.getMonth()
  const dayNum = date.getDate()

  const isToday =
    dayNum === today.getDate() &&
    m === today.getMonth() &&
    y === today.getFullYear()

  // Match events occurring on this date
  const cellEvents = eventsStore.filteredEvents.filter((ev) => {
    const evStart = new Date(ev.start_at)
    return (
      evStart.getDate() === dayNum &&
      evStart.getMonth() === m &&
      evStart.getFullYear() === y
    )
  })

  return {
    date,
    dateStr: `${y}-${m}-${dayNum}`,
    dayNumber: dayNum,
    isCurrentMonth,
    isToday,
    events: cellEvents,
  }
}

function handleCellClick(date: Date) {
  eventsStore.openCreateModal(date)
}
</script>
