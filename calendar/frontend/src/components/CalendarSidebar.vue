<template>
  <aside class="w-64 h-full bg-white border-r border-cal-border flex flex-col p-4 shrink-0 overflow-y-auto select-none">
    <!-- "+ Create" Button -->
    <div class="mb-4">
      <button
        @click="eventsStore.openCreateModal()"
        class="w-full flex items-center justify-center gap-3 px-6 py-3 bg-white hover:bg-gray-50 border border-gray-200 rounded-full shadow-md hover:shadow-lg transition-all text-sm font-medium text-gray-700 active:scale-[0.98]"
      >
        <span class="text-xl font-bold text-cal-blue">＋</span>
        <span>Create</span>
      </button>
    </div>

    <!-- Mini Month Widget -->
    <div class="mb-6 rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <MiniDatePicker />
    </div>

    <!-- Meet Video Conferencing Quick Link -->
    <div class="mb-6 p-3 bg-blue-50/70 border border-blue-100 rounded-xl space-y-2">
      <div class="flex items-center gap-2 text-xs font-semibold text-cal-blue">
        <Video :size="15" />
        <span>Sidaz Meet Synced</span>
      </div>
      <p class="text-[11px] text-gray-600 leading-tight">
        Video meetings created here or in Sidaz Meet are automatically synchronized.
      </p>
      <a
        :href="meetUrl"
        target="_blank"
        class="inline-flex items-center gap-1 text-[11px] font-semibold text-cal-blue hover:underline"
      >
        <span>Open Meet App</span>
        <ExternalLink :size="11" />
      </a>
    </div>

    <!-- My Calendars Section -->
    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs font-semibold text-gray-600 tracking-wider uppercase">
        <span>My calendars</span>
        <button
          @click="isAddCalendarOpen = !isAddCalendarOpen"
          class="p-1 hover:bg-gray-100 rounded-full text-gray-500"
          title="Add other calendar"
        >
          <Plus :size="14" />
        </button>
      </div>

      <!-- Add Calendar Inline Form -->
      <div v-if="isAddCalendarOpen" class="p-2 bg-gray-50 rounded-lg space-y-2 border border-gray-200">
        <input
          v-model="newCalendarName"
          type="text"
          placeholder="Calendar name"
          class="w-full px-2 py-1 bg-white border border-gray-300 rounded text-xs outline-none focus:border-cal-blue"
          @keyup.enter="handleCreateCalendar"
        />
        <div class="flex justify-end gap-1">
          <button
            @click="isAddCalendarOpen = false"
            class="px-2 py-0.5 text-[11px] text-gray-500 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            @click="handleCreateCalendar"
            :disabled="!newCalendarName.trim()"
            class="px-2.5 py-0.5 bg-cal-blue text-white rounded text-[11px] font-medium disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </div>

      <!-- Calendars Checkboxes -->
      <div class="space-y-1">
        <label
          v-for="cal in eventsStore.calendars"
          :key="cal.id"
          class="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors text-xs text-gray-700"
        >
          <input
            type="checkbox"
            :checked="eventsStore.selectedCalendarIds.includes(cal.id)"
            @change="eventsStore.toggleCalendarSelection(cal.id)"
            class="w-4 h-4 rounded text-cal-blue focus:ring-0 cursor-pointer"
            :style="{ accentColor: cal.color || '#1a73e8' }"
          />
          <span class="truncate font-medium">{{ cal.name }}</span>
        </label>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Video, Plus, ExternalLink } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'
import { api } from '@/lib/api'
import MiniDatePicker from '@/components/MiniDatePicker.vue'

const eventsStore = useEventsStore()
const meetUrl = import.meta.env.VITE_MEET_APP_URL || 'https://frontend-seven-theta-86.vercel.app'

const isAddCalendarOpen = ref(false)
const newCalendarName = ref('')

async function handleCreateCalendar() {
  if (!newCalendarName.value.trim()) return
  try {
    const res = await api.post('/calendars', {
      name: newCalendarName.value.trim(),
      color: '#0b8043',
    })
    eventsStore.calendars.push(res.data)
    eventsStore.selectedCalendarIds.push(res.data.id)
    newCalendarName.value = ''
    isAddCalendarOpen.value = false
  } catch (e) {
    console.warn('Failed to add calendar:', e)
  }
}
</script>
