<template>
  <div class="min-h-screen w-full flex items-center justify-center p-4 bg-[#202124]">
    <div class="w-full max-w-md bg-[#303134] border border-meet-border rounded-2xl p-8 shadow-2xl space-y-6">
      <!-- Logo & Title -->
      <div class="text-center space-y-2">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-meet-blue text-white mb-2 shadow-lg">
          <Video :size="28" />
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight">Create your account</h1>
        <p class="text-sm text-meet-textMuted">Join meetings with persistent identity & host controls</p>
      </div>

      <!-- Error alert -->
      <div v-if="errorMessage" class="p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-300 text-xs">
        {{ errorMessage }}
      </div>

      <!-- Success alert -->
      <div v-if="successMessage" class="p-3 bg-green-500/20 border border-green-500/30 rounded-xl text-green-300 text-xs">
        {{ successMessage }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSignup" class="space-y-4">
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            Your Full Name
          </label>
          <input
            v-model="displayName"
            type="text"
            required
            placeholder="Jane Doe"
            class="w-full px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
          />
        </div>

        <div class="space-y-1.5">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            Email Address
          </label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="you@example.com"
            class="w-full px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
          />
        </div>

        <div class="space-y-1.5">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            Password
          </label>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            placeholder="At least 6 characters"
            class="w-full px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
          />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3 bg-meet-blue hover:bg-meet-blue-hover disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-all shadow-md mt-2 flex items-center justify-center gap-2"
        >
          <span v-if="isLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <span>{{ isLoading ? 'Creating account...' : 'Create Account' }}</span>
        </button>
      </form>

      <!-- Footer links -->
      <div class="pt-4 border-t border-meet-border text-center text-xs text-meet-textMuted">
        <p>
          Already have an account?
          <RouterLink to="/login" class="text-meet-primary hover:underline font-medium ml-1">
            Sign in
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Video } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const displayName = ref('')
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function handleSignup() {
  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await authStore.signup(email.value, password.value, displayName.value)
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to create account. Please check your details.'
  } finally {
    isLoading.value = false
  }
}
</script>
