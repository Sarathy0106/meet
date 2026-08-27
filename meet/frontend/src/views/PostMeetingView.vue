<template>
  <div class="min-h-screen w-full flex flex-col items-center justify-center bg-[#202124] text-white p-6 select-none">
    <div class="max-w-md w-full text-center space-y-6 bg-[#303134] border border-meet-border rounded-3xl p-8 shadow-2xl">
      <div class="w-16 h-16 rounded-2xl bg-meet-blue/20 text-meet-primary flex items-center justify-center mx-auto">
        <PhoneOff :size="32" />
      </div>

      <div class="space-y-2">
        <h1 class="text-2xl font-medium text-white">You left the meeting</h1>
        <p class="text-xs text-meet-textMuted leading-relaxed">
          Thanks for using sidaz-meet. Your meeting chat is saved in your history.
        </p>
      </div>

      <div class="pt-4 flex flex-col sm:flex-row gap-3 justify-center">
        <button
          v-if="meetingCode"
          @click="rejoin"
          class="px-6 py-2.5 bg-meet-blue hover:bg-meet-blue-hover text-white text-sm font-medium rounded-full shadow transition-colors"
        >
          Rejoin
        </button>
        <button
          @click="goHome"
          class="px-6 py-2.5 bg-meet-surfaceLight hover:bg-meet-border text-white text-sm font-medium rounded-full transition-colors"
        >
          Return to home screen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhoneOff } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const meetingCode = computed(() => route.params.code as string)

function rejoin() {
  if (meetingCode.value) {
    router.push(`/meet/${meetingCode.value}`)
  } else {
    router.push('/')
  }
}

function goHome() {
  router.push('/')
}
</script>
