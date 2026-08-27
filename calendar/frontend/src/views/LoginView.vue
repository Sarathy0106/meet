<template>
  <div class="min-h-screen w-full bg-gray-50 flex items-center justify-center p-4 select-none">
    <div class="max-w-md w-full bg-white border border-gray-200 rounded-3xl shadow-xl p-8 space-y-6">
      <!-- App Brand -->
      <div class="text-center space-y-2">
        <div class="w-12 h-12 rounded-2xl bg-cal-blue text-white font-bold text-xl flex items-center justify-center shadow mx-auto">
          M
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Meridian Calendar</h1>
        <p class="text-xs text-gray-500">Sign in to sync your schedule & Meet meetings</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-700">Email Address</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="you@example.com"
            class="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-xl text-sm outline-none focus:border-cal-blue transition-colors"
          />
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-700">Display Name</label>
          <input
            v-model="displayName"
            type="text"
            required
            placeholder="Your Name"
            class="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-xl text-sm outline-none focus:border-cal-blue transition-colors"
          />
        </div>

        <button
          type="submit"
          class="w-full py-3 bg-cal-blue hover:bg-cal-blueHover text-white rounded-xl text-sm font-semibold shadow transition-all active:scale-[0.99]"
        >
          Continue to Calendar
        </button>
      </form>

      <!-- Shortcut to Meet App -->
      <div class="pt-4 border-t border-gray-100 text-center">
        <a
          :href="meetUrl"
          target="_blank"
          class="inline-flex items-center gap-1.5 text-xs text-cal-blue hover:underline font-medium"
        >
          <span>Open Sidaz Meet</span>
          <ExternalLink :size="12" />
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ExternalLink } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const displayName = ref('')
const meetUrl = import.meta.env.VITE_MEET_APP_URL || 'https://frontend-seven-theta-86.vercel.app'

const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!email.value.trim()) return

  isLoading.value = true
  errorMessage.value = ''
  try {
    await authStore.login(email.value.trim())
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to sign in. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
