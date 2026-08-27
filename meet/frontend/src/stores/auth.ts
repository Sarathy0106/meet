import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(
    localStorage.getItem('sidaz_user') ? JSON.parse(localStorage.getItem('sidaz_user')!) : null
  )
  const token = ref<string | null>(localStorage.getItem('sidaz_access_token'))
  const guestName = ref<string>(localStorage.getItem('sidaz_guest_name') || '')

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const displayName = computed(() => {
    if (user.value) return user.value.display_name
    if (guestName.value) return guestName.value
    return 'Guest'
  })

  function setAuth(authData: { user: User; access_token: string; refresh_token: string }) {
    user.value = authData.user
    token.value = authData.access_token
    localStorage.setItem('sidaz_user', JSON.stringify(authData.user))
    localStorage.setItem('sidaz_access_token', authData.access_token)
    localStorage.setItem('sidaz_refresh_token', authData.refresh_token)
  }

  function setGuestName(name: string) {
    guestName.value = name
    localStorage.setItem('sidaz_guest_name', name)
  }

  async function login(email: string, password: string) {
    const res = await api.post('/auth/login', { email, password })
    setAuth(res.data)
    return res.data
  }

  async function signup(email: string, password: string, displayName: string) {
    const res = await api.post('/auth/signup', { email, password, display_name: displayName })
    setAuth(res.data)
    return res.data
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const res = await api.get('/auth/me')
      user.value = res.data
      localStorage.setItem('sidaz_user', JSON.stringify(res.data))
      return res.data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('sidaz_user')
    localStorage.removeItem('sidaz_access_token')
    localStorage.removeItem('sidaz_refresh_token')
  }

  return {
    user,
    token,
    guestName,
    isAuthenticated,
    displayName,
    setAuth,
    setGuestName,
    login,
    signup,
    fetchMe,
    logout,
  }
})
