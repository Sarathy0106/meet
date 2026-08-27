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

  async function initSession() {
    if (token.value) {
      try {
        const res = await api.get('/auth/me')
        user.value = res.data
        isInitialized.value = true
        return
      } catch (err: any) {
        if (err.response?.status === 401) {
          token.value = ''
          localStorage.removeItem('access_token')
          localStorage.removeItem('token')
        }
      }
    }

    // Auto-create / join guest session if unauthenticated
    try {
      const res = await api.post('/auth/guest')
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('access_token', res.data.access_token)
    } catch (e) {
      console.warn('Could not auto-provision session:', e)
    } finally {
      isInitialized.value = true
    }
  }

  async function login(email: string, password?: string) {
    if (password) {
      const res = await api.post('/auth/login', { email, password })
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('access_token', res.data.access_token)
      return res.data
    } else {
      const res = await api.post('/auth/guest', { email })
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('access_token', res.data.access_token)
      return res.data
    }
  }

  async function signup(email: string, password: string, displayName: string) {
    const res = await api.post('/auth/signup', { email, password, display_name: displayName })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access_token)
    return res.data
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
    initSession,
    login,
    signup,
    logout,
  }
})
