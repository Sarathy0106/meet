<template>
  <!-- If Public RSVP View or Login View -->
  <div v-if="isStandaloneView" class="w-full h-full min-h-screen">
    <router-view />
  </div>

  <!-- Main Calendar Layout -->
  <div v-else class="h-screen w-screen flex flex-col bg-white overflow-hidden">
    <!-- Top Header -->
    <CalendarHeader />

    <!-- Main Workspace (Sidebar + Calendar Views) -->
    <div class="flex-1 flex overflow-hidden">
      <CalendarSidebar class="hidden md:flex" />

      <!-- Active Calendar View (Month / Week / Day) -->
      <main class="flex-1 h-full min-w-0 flex flex-col relative overflow-hidden">
        <MonthView v-if="eventsStore.currentView === 'month'" />
        <WeekView v-else-if="eventsStore.currentView === 'week'" />
        <DayView v-else-if="eventsStore.currentView === 'day'" />
      </main>
    </div>

    <!-- Modals & Drawers -->
    <CreateEventModal />
    <EventDetailModal />
    <NotificationCenter />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'
import CalendarHeader from '@/components/CalendarHeader.vue'
import CalendarSidebar from '@/components/CalendarSidebar.vue'
import CreateEventModal from '@/components/CreateEventModal.vue'
import EventDetailModal from '@/components/EventDetailModal.vue'
import NotificationCenter from '@/components/NotificationCenter.vue'
import MonthView from '@/views/MonthView.vue'
import WeekView from '@/views/WeekView.vue'
import DayView from '@/views/DayView.vue'

const route = useRoute()
const eventsStore = useEventsStore()
const authStore = useAuthStore()
const notifStore = useNotificationStore()

const isStandaloneView = computed(() => {
  return route.name === 'public-rsvp' || route.name === 'login'
})

onMounted(async () => {
  await authStore.fetchCurrentUser()
  await eventsStore.fetchCalendars()
  await eventsStore.fetchEvents()
  await notifStore.fetchNotifications()
})
</script>
