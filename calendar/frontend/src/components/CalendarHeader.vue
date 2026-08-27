<template>
  <header class="h-16 px-4 sm:px-6 bg-white border-b border-cal-border flex items-center justify-between z-30 select-none">
    <!-- Left Section: Logo & Date Navigation -->
    <div class="flex items-center gap-3 sm:gap-6">
      <!-- App Brand -->
      <div class="flex items-center gap-2.5 cursor-pointer" @click="eventsStore.today()">
        <div class="w-9 h-9 rounded-xl bg-cal-blue flex items-center justify-center text-white shadow-sm font-bold text-base">
          M
        </div>
        <div class="hidden sm:flex items-center gap-1">
          <span class="font-semibold text-lg text-gray-800 tracking-tight">Meridian</span>
          <span class="font-light text-lg text-cal-textMuted">Calendar</span>
        </div>
      </div>

      <!-- Navigation: Today, <, > -->
      <div class="flex items-center gap-2">
        <button
          @click="eventsStore.today()"
          class="px-4 py-1.5 border border-gray-300 hover:bg-gray-100 rounded-lg text-xs font-semibold text-gray-700 transition-colors shadow-sm"
        >
          Today
        </button>

        <div class="flex items-center">
          <button
            @click="eventsStore.prev()"
            class="p-2 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
            title="Previous period"
          >
            <ChevronLeft :size="18" />
          </button>
          <button
            @click="eventsStore.next()"
            class="p-2 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
            title="Next period"
          >
            <ChevronRight :size="18" />
          </button>
        </div>

        <!-- Month & Year Title -->
        <h2 class="text-base sm:text-lg font-medium text-gray-800 ml-1">
          {{ formattedHeaderDate }}
        </h2>
      </div>
    </div>

    <!-- Right Section: View Switcher, Notifications, User Profile -->
    <div class="flex items-center gap-2 sm:gap-4">
      <!-- View Mode Selector (Month / Week / Day) -->
      <div class="flex items-center bg-gray-100 p-1 rounded-xl border border-gray-200 text-xs font-medium">
        <button
          v-for="mode in (['month', 'week', 'day'] as const)"
          :key="mode"
          @click="eventsStore.setView(mode)"
          class="px-3 py-1.5 rounded-lg capitalize transition-all"
          :class="
            eventsStore.currentView === mode
              ? 'bg-white text-cal-blue shadow-sm font-semibold'
              : 'text-gray-600 hover:text-gray-900'
          "
        >
          {{ mode }}
        </button>
      </div>

      <!-- Notification Bell -->
      <button
        @click="notifStore.toggleNotificationCenter()"
        class="relative p-2.5 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
        title="Reminders & Notifications"
      >
        <Bell :size="18" />
        <span
          v-if="notifStore.unreadCount > 0"
          class="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center"
        >
          {{ notifStore.unreadCount }}
        </span>
      </button>

      <!-- User Profile / Auth Initials -->
      <div class="flex items-center gap-2 pl-2 border-l border-gray-200">
        <div
          class="w-8 h-8 rounded-full bg-cal-blue text-white font-semibold text-xs flex items-center justify-center shadow-sm cursor-pointer"
          :title="authStore.displayName"
        >
          {{ authStore.displayName.slice(0, 2).toUpperCase() }}
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight, Bell } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'

const eventsStore = useEventsStore()
const authStore = useAuthStore()
const notifStore = useNotificationStore()

const monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const formattedHeaderDate = computed(() => {
  const d = eventsStore.currentDate
  if (eventsStore.currentView === 'day') {
    return `${monthNames[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`
  }
  return `${monthNames[d.getMonth()]} ${d.getFullYear()}`
})
</script>
