import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('access_token') || localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const isInitialized = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const displayName = computed(() => user.value?.display_name || user.value?.email || 'User')

  async function fetchCurrentUser() {
    if (!token.value) {
      isInitialized.value = true
      return
    }
    try {
      const res = await api.get('/auth/me')
      user.value = res.data
    } catch {
      // Fallback guest / demo user if offline or local testing
      user.value = {
        id: '00000000-0000-0000-0000-000000000001',
        email: 'user@sidanex.com',
        display_name: 'Demo User',
      }
    } finally {
      isInitialized.value = true
    }
  }

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
    fetchCurrentUser()
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isInitialized,
    isAuthenticated,
    displayName,
    fetchCurrentUser,
    setToken,
    logout,
  }
})
