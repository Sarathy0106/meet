<template>
  <div
    v-if="notifStore.isNotificationCenterOpen"
    class="fixed inset-0 z-40 bg-black/20 backdrop-blur-xs flex justify-end"
    @click.self="notifStore.toggleNotificationCenter()"
  >
    <div
      class="w-full max-w-sm h-full bg-white border-l border-cal-border shadow-2xl flex flex-col select-none animate-in slide-in-from-right duration-200"
    >
      <!-- Header -->
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/70">
        <div class="flex items-center gap-2">
          <Bell :size="18" class="text-cal-blue" />
          <h3 class="text-sm font-semibold text-gray-800">Notifications & Reminders</h3>
        </div>
        <button
          @click="notifStore.toggleNotificationCenter()"
          class="p-1 rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-700"
        >
          <X :size="16" />
        </button>
      </div>

      <!-- Web Push Banner / Toggle -->
      <div class="p-3.5 bg-blue-50/80 border-b border-blue-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Smartphone :size="16" class="text-cal-blue shrink-0" />
          <div class="text-[11px] leading-tight text-gray-700">
            <p class="font-medium">Browser Push Alerts</p>
            <p class="text-gray-500">Get notified even when closed</p>
          </div>
        </div>
        <button
          @click="handleEnablePush"
          :disabled="isPushSubscribing"
          class="px-2.5 py-1 bg-cal-blue hover:bg-cal-blueHover text-white text-[11px] font-semibold rounded-md shadow-xs transition-colors"
        >
          {{ isPushSubscribing ? 'Enabling...' : 'Enable' }}
        </button>
      </div>

      <!-- Actions Bar -->
      <div v-if="notifStore.notifications.length > 0" class="px-5 py-2 border-b border-gray-100 flex justify-end">
        <button
          @click="notifStore.markAllAsRead()"
          class="text-[11px] text-cal-blue hover:underline font-medium"
        >
          Mark all as read
        </button>
      </div>

      <!-- Notifications List -->
      <div class="flex-1 overflow-y-auto p-4 space-y-2.5">
        <div
          v-if="notifStore.notifications.length === 0"
          class="h-48 flex flex-col items-center justify-center text-center text-gray-400 space-y-2"
        >
          <BellOff :size="28" class="text-gray-300" />
          <p class="text-xs">No new notifications</p>
        </div>

        <div
          v-for="notif in notifStore.notifications"
          :key="notif.id"
          @click="handleNotificationClick(notif)"
          class="p-3 rounded-xl border transition-all cursor-pointer"
          :class="
            notif.is_read
              ? 'bg-white border-gray-100 text-gray-600'
              : 'bg-blue-50/40 border-blue-100 text-gray-900 shadow-xs'
          "
        >
          <div class="flex items-start justify-between gap-2">
            <h4 class="text-xs font-semibold leading-snug">{{ notif.title }}</h4>
            <span v-if="!notif.is_read" class="w-2 h-2 rounded-full bg-cal-blue shrink-0 mt-1"></span>
          </div>
          <p class="text-[11px] text-gray-500 mt-1 leading-normal">{{ notif.message }}</p>
          <span class="text-[10px] text-gray-400 mt-1.5 block">
            {{ formatTime(notif.created_at) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Bell, BellOff, X, Smartphone } from 'lucide-vue-next'
import { useNotificationStore } from '@/stores/notifications'
import { useEventsStore } from '@/stores/events'
import type { InAppNotificationItem } from '@/types'

const notifStore = useNotificationStore()
const eventsStore = useEventsStore()
const isPushSubscribing = ref(false)

async function handleEnablePush() {
  isPushSubscribing.value = true
  try {
    const success = await notifStore.enablePushNotifications()
    if (success) {
      alert('Browser push notifications enabled successfully!')
    } else {
      alert('Please allow notification permissions in your browser address bar.')
    }
  } finally {
    isPushSubscribing.value = false
  }
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function handleNotificationClick(notif: InAppNotificationItem) {
  notifStore.markAsRead(notif.id)
  if (notif.event_id) {
    const ev = eventsStore.events.find((e) => e.id === notif.event_id)
    if (ev) {
      eventsStore.openDetailModal(ev)
      notifStore.toggleNotificationCenter()
    }
  }
}
</script>
