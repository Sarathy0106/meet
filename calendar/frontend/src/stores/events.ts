import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { CalendarEvent, CalendarInfo } from '@/types'

export const useEventsStore = defineStore('events', () => {
  const currentDate = ref<Date>(new Date())
  const currentView = ref<'month' | 'week' | 'day'>('month')
  const events = ref<CalendarEvent[]>([])
  const calendars = ref<CalendarInfo[]>([])
  const selectedCalendarIds = ref<string[]>([])
  const isLoading = ref(false)

  // Modals state
  const isCreateModalOpen = ref(false)
  const isDetailModalOpen = ref(false)
  const selectedEvent = ref<CalendarEvent | null>(null)
  const createModalDefaultDate = ref<Date>(new Date())

  const activeCalendars = computed(() => {
    return calendars.value.filter((c) => selectedCalendarIds.value.includes(c.id))
  })

  const filteredEvents = computed(() => {
    if (selectedCalendarIds.value.length === 0) {
      return events.value
    }
    return events.value.filter((e) => selectedCalendarIds.value.includes(e.calendar_id))
  })

  async function fetchCalendars() {
    try {
      const res = await api.get('/calendars')
      calendars.value = res.data
      if (selectedCalendarIds.value.length === 0) {
        selectedCalendarIds.value = calendars.value.map((c) => c.id)
      }
    } catch (e) {
      console.warn('Failed to fetch calendars:', e)
    }
  }

  async function fetchEvents(rangeStart?: Date, rangeEnd?: Date) {
    isLoading.value = true
    try {
      const start = rangeStart || new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
      const end = rangeEnd || new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 2, 0)

      const res = await api.get('/events', {
        params: {
          from: start.toISOString(),
          to: end.toISOString(),
        },
      })
      events.value = res.data
    } catch (e) {
      console.warn('Failed to fetch events:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function createEvent(payload: any) {
    const res = await api.post('/events', payload)
    await fetchEvents()
    return res.data
  }

  async function updateEvent(id: string, payload: any) {
    const res = await api.patch(`/events/${id}`, payload)
    await fetchEvents()
    if (selectedEvent.value?.id === id) {
      selectedEvent.value = res.data
    }
    return res.data
  }

  async function deleteEvent(id: string) {
    await api.delete(`/events/${id}`)
    events.value = events.value.filter((e) => e.id !== id && e.parent_id !== id)
    closeDetailModal()
  }

  async function rsvpEvent(eventId: string, status: 'yes' | 'no' | 'maybe') {
    await api.post(`/events/${eventId}/rsvp`, { status })
    await fetchEvents()
    if (selectedEvent.value?.id === eventId) {
      const updated = events.value.find((e) => e.id === eventId)
      if (updated) selectedEvent.value = updated
    }
  }

  async function resendInvites(eventId: string) {
    const res = await api.post(`/events/${eventId}/invite`)
    return res.data
  }

  function downloadICS(eventId: string) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
    window.open(`${baseUrl}/events/${eventId}/ics`, '_blank')
  }

  // Modal actions
  function openCreateModal(defaultDate?: Date) {
    createModalDefaultDate.value = defaultDate || new Date()
    isCreateModalOpen.value = true
  }

  function closeCreateModal() {
    isCreateModalOpen.value = false
  }

  function openDetailModal(event: CalendarEvent) {
    selectedEvent.value = event
    isDetailModalOpen.value = true
  }

  function closeDetailModal() {
    isDetailModalOpen.value = false
    selectedEvent.value = null
  }

  // Navigation helpers
  function next() {
    const d = new Date(currentDate.value)
    if (currentView.value === 'month') {
      d.setMonth(d.getMonth() + 1)
    } else if (currentView.value === 'week') {
      d.setDate(d.getDate() + 7)
    } else {
      d.setDate(d.getDate() + 1)
    }
    currentDate.value = d
    fetchEvents()
  }

  function prev() {
    const d = new Date(currentDate.value)
    if (currentView.value === 'month') {
      d.setMonth(d.getMonth() - 1)
    } else if (currentView.value === 'week') {
      d.setDate(d.getDate() - 7)
    } else {
      d.setDate(d.getDate() - 1)
    }
    currentDate.value = d
    fetchEvents()
  }

  function today() {
    currentDate.value = new Date()
    fetchEvents()
  }

  function setDate(date: Date) {
    currentDate.value = new Date(date)
    fetchEvents()
  }

  function setView(view: 'month' | 'week' | 'day') {
    currentView.value = view
  }

  function toggleCalendarSelection(id: string) {
    if (selectedCalendarIds.value.includes(id)) {
      selectedCalendarIds.value = selectedCalendarIds.value.filter((calId) => calId !== id)
    } else {
      selectedCalendarIds.value.push(id)
    }
  }

  return {
    currentDate,
    currentView,
    events,
    calendars,
    selectedCalendarIds,
    isLoading,
    isCreateModalOpen,
    isDetailModalOpen,
    selectedEvent,
    createModalDefaultDate,
    activeCalendars,
    filteredEvents,
    fetchCalendars,
    fetchEvents,
    createEvent,
    updateEvent,
    deleteEvent,
    rsvpEvent,
    resendInvites,
    downloadICS,
    openCreateModal,
    closeCreateModal,
    openDetailModal,
    closeDetailModal,
    next,
    prev,
    today,
    setDate,
    setView,
    toggleCalendarSelection,
  }
})
