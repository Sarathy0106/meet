<template>
  <div class="p-3 bg-white select-none">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <span class="text-xs font-semibold text-gray-800">
        {{ currentMonthName }} {{ viewDate.getFullYear() }}
      </span>
      <div class="flex items-center gap-1">
        <button
          @click="prevMonth"
          class="p-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ChevronLeft :size="14" />
        </button>
        <button
          @click="nextMonth"
          class="p-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ChevronRight :size="14" />
        </button>
      </div>
    </div>

    <!-- Day of week headers -->
    <div class="grid grid-cols-7 text-center text-[10px] font-medium text-gray-400 mb-1">
      <span v-for="d in ['S', 'M', 'T', 'W', 'T', 'F', 'S']" :key="d">{{ d }}</span>
    </div>

    <!-- Days Matrix -->
    <div class="grid grid-cols-7 gap-y-1 text-center text-xs">
      <button
        v-for="cell in monthCells"
        :key="cell.date.toISOString()"
        @click="selectDate(cell.date)"
        class="w-6 h-6 mx-auto flex items-center justify-center rounded-full transition-colors text-[11px]"
        :class="[
          cell.isCurrentMonth ? 'text-gray-800' : 'text-gray-300',
          isToday(cell.date) ? 'bg-cal-blue text-white font-bold' : '',
          isSelected(cell.date) && !isToday(cell.date) ? 'bg-blue-100 text-cal-blue font-semibold' : 'hover:bg-gray-100',
        ]"
      >
        {{ cell.date.getDate() }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'

const eventsStore = useEventsStore()
const viewDate = ref(new Date(eventsStore.currentDate))

const monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const currentMonthName = computed(() => monthNames[viewDate.value.getMonth()])

interface Cell {
  date: Date
  isCurrentMonth: boolean
}

const monthCells = computed<Cell[]>(() => {
  const year = viewDate.value.getFullYear()
  const month = viewDate.value.getMonth()

  const firstDayOfMonth = new Date(year, month, 1)
  const startDay = firstDayOfMonth.getDay() // 0 = Sun

  const cells: Cell[] = []

  // Preceding days from prev month
  for (let i = startDay - 1; i >= 0; i--) {
    cells.push({
      date: new Date(year, month, -i),
      isCurrentMonth: false,
    })
  }

  // Days in current month
  const totalDays = new Date(year, month + 1, 0).getDate()
  for (let i = 1; i <= totalDays; i++) {
    cells.push({
      date: new Date(year, month, i),
      isCurrentMonth: true,
    })
  }

  // Next month trailing days to complete 35 or 42 grid
  const remaining = 35 - cells.length
  if (remaining > 0) {
    for (let i = 1; i <= remaining; i++) {
      cells.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false,
      })
    }
  }

  return cells
})

function prevMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() - 1)
  viewDate.value = d
}

function nextMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() + 1)
  viewDate.value = d
}

function isToday(date: Date) {
  const today = new Date()
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  )
}

function isSelected(date: Date) {
  const sel = eventsStore.currentDate
  return (
    date.getDate() === sel.getDate() &&
    date.getMonth() === sel.getMonth() &&
    date.getFullYear() === sel.getFullYear()
  )
}

function selectDate(date: Date) {
  eventsStore.setDate(date)
}
</script>
