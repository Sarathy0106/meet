import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import { registerPushNotifications } from '@/lib/push'
import type { InAppNotificationItem } from '@/types'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<InAppNotificationItem[]>([])
  const isPushEnabled = ref(false)
  const isNotificationCenterOpen = ref(false)

  const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

  async function fetchNotifications() {
    try {
      const res = await api.get('/notifications')
      notifications.value = res.data
    } catch {
      // Local fallback
    }
  }

  async function markAsRead(id: string) {
    try {
      await api.patch(`/notifications/${id}/read`)
      const target = notifications.value.find((n) => n.id === id)
      if (target) target.is_read = true
    } catch {}
  }

  async function markAllAsRead() {
    try {
      await api.post('/notifications/read-all')
      notifications.value.forEach((n) => (n.is_read = true))
    } catch {}
  }

  async function enablePushNotifications() {
    const success = await registerPushNotifications()
    isPushEnabled.value = success
    return success
  }

  function toggleNotificationCenter() {
    isNotificationCenterOpen.value = !isNotificationCenterOpen.value
    if (isNotificationCenterOpen.value) {
      fetchNotifications()
    }
  }

  return {
    notifications,
    isPushEnabled,
    isNotificationCenterOpen,
    unreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    enablePushNotifications,
    toggleNotificationCenter,
  }
})
