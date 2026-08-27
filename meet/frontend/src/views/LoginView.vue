<template>
  <div class="min-h-screen w-full flex items-center justify-center p-4 bg-[#202124]">
    <div class="w-full max-w-md bg-[#303134] border border-meet-border rounded-2xl p-8 shadow-2xl space-y-6">
      <!-- Logo & Title -->
      <div class="text-center space-y-2">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-meet-blue text-white mb-2 shadow-lg">
          <Video :size="28" />
        </div>
        <h1 class="text-2xl font-bold text-white tracking-tight">Sign in to sidaz-meet</h1>
        <p class="text-sm text-meet-textMuted">Premium video meetings for everyone</p>
      </div>

      <!-- Error alert -->
      <div v-if="errorMessage" class="p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-300 text-xs">
        {{ errorMessage }}
      </div>

      <!-- Success alert -->
      <div v-if="successMessage" class="p-3 bg-green-500/20 border border-green-500/30 rounded-xl text-green-300 text-xs">
        {{ successMessage }}
      </div>

      <!-- Mode Selector Tabs: Password vs Email OTP -->
      <div class="flex p-1 bg-[#202124] rounded-xl border border-meet-border">
        <button
          type="button"
          @click="authMode = 'password'"
          class="flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors"
          :class="authMode === 'password' ? 'bg-[#303134] text-white shadow' : 'text-meet-textMuted hover:text-white'"
        >
          Password
        </button>
        <button
          type="button"
          @click="authMode = 'otp'"
          class="flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors"
          :class="authMode === 'otp' ? 'bg-[#303134] text-white shadow' : 'text-meet-textMuted hover:text-white'"
        >
          Email OTP
        </button>
      </div>

      <!-- Password Login Form -->
      <form v-if="authMode === 'password'" @submit.prevent="handleLogin" class="space-y-4">
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
            placeholder="••••••••"
            class="w-full px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
          />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3 bg-meet-blue hover:bg-meet-blue-hover disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-all shadow-md mt-2 flex items-center justify-center gap-2"
        >
          <span v-if="isLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <span>{{ isLoading ? 'Signing in...' : 'Sign In' }}</span>
        </button>
      </form>

      <!-- Email OTP Login Form -->
      <div v-else class="space-y-4">
        <div class="space-y-1.5">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            Email Address
          </label>
          <div class="flex gap-2">
            <input
              v-model="otpEmail"
              type="email"
              required
              placeholder="you@example.com"
              class="flex-1 px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none transition-colors"
            />
            <button
              type="button"
              @click="handleSendOTP"
              :disabled="isSendingOTP || !otpEmail.trim()"
              class="px-4 py-2.5 bg-meet-surfaceLight hover:bg-meet-border disabled:opacity-50 text-white text-xs font-medium rounded-xl shrink-0 transition-colors"
            >
              {{ isSendingOTP ? 'Sending...' : 'Get Code' }}
            </button>
          </div>
        </div>

        <div v-if="otpSent" class="space-y-1.5">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            6-Digit Verification Code
          </label>
          <input
            v-model="otpCode"
            type="text"
            required
            maxlength="6"
            placeholder="123456"
            class="w-full px-4 py-2.5 bg-[#202124] border border-meet-border rounded-xl text-white text-sm tracking-widest text-center font-mono focus:border-meet-primary outline-none transition-colors"
          />
        </div>

        <button
          v-if="otpSent"
          type="button"
          @click="handleVerifyOTP"
          :disabled="isLoading || !otpCode.trim()"
          class="w-full py-3 bg-meet-blue hover:bg-meet-blue-hover disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-all shadow-md flex items-center justify-center gap-2"
        >
          <span v-if="isLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <span>Verify & Sign In</span>
        </button>
      </div>

      <!-- Footer links -->
      <div class="pt-4 border-t border-meet-border text-center text-xs text-meet-textMuted space-y-2">
        <p>
          Don't have an account?
          <RouterLink to="/signup" class="text-meet-primary hover:underline font-medium ml-1">
            Sign up
          </RouterLink>
        </p>
        <p>
          <RouterLink to="/" class="hover:underline">
            ← Continue as Guest to Dashboard
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
import { api } from '@/lib/api'

const router = useRouter()
const authStore = useAuthStore()

const authMode = ref<'password' | 'otp'>('password')
const email = ref('')
const password = ref('')
const otpEmail = ref('')
const otpCode = ref('')
const otpSent = ref(false)
const isSendingOTP = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function handleLogin() {
  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to sign in. Please check your credentials.'
  } finally {
    isLoading.value = false
  }
}

async function handleSendOTP() {
  if (!otpEmail.value.trim()) return
  isSendingOTP.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await api.post('/auth/otp/send', { email: otpEmail.value.trim() })
    otpSent.value = true
    successMessage.value = 'Verification code sent to your email!'
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to send OTP code.'
  } finally {
    isSendingOTP.value = false
  }
}

async function handleVerifyOTP() {
  if (!otpCode.value.trim()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const res = await api.post('/auth/otp/verify', {
      email: otpEmail.value.trim(),
      otp_code: otpCode.value.trim(),
    })
    authStore.setAuth(res.data)
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Invalid or expired verification code.'
  } finally {
    isLoading.value = false
  }
}
</script>
