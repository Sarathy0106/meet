<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 select-none animate-in fade-in duration-200"
  >
    <div
      class="w-full max-w-lg bg-[#202124] border border-meet-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"
      @click.stop
    >
      <!-- Header -->
      <div class="px-6 py-4 border-b border-meet-border flex items-center justify-between bg-[#292a2d]">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-meet-red/20 text-meet-red">
            <Lock :size="20" />
          </div>
          <div>
            <h2 class="text-base font-semibold text-white">
              {{ title }}
            </h2>
            <p class="text-xs text-meet-textMuted">
              Browser permission is needed for your media
            </p>
          </div>
        </div>
        <button
          @click="close"
          class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Body / Steps -->
      <div class="p-6 space-y-5">
        <p class="text-xs text-gray-300 leading-relaxed">
          Your browser has blocked or restricted access to your
          <strong class="text-white">{{ targetDeviceText }}</strong>. Follow these quick steps to allow access:
        </p>

        <!-- Visual Step 1: Address bar icon -->
        <div class="p-3.5 rounded-xl bg-[#28292c] border border-white/5 space-y-3">
          <div class="flex items-start gap-3">
            <div class="w-6 h-6 rounded-full bg-meet-blue/20 text-meet-blue text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
              1
            </div>
            <div class="text-xs text-gray-300">
              <p class="font-medium text-white mb-1">Click the lock or site settings icon</p>
              <p>Look at the left side of your browser's address bar at the top of your screen.</p>
              <div class="mt-2 inline-flex items-center gap-2 px-3 py-1.5 bg-[#1e1f22] rounded-lg border border-meet-border text-[11px] text-meet-textMuted font-mono">
                <Lock :size="12" class="text-meet-primary" />
                <span class="text-white">meet.example.com</span>
                <span class="text-emerald-400">🔒</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Visual Step 2: Toggle Allow -->
        <div class="p-3.5 rounded-xl bg-[#28292c] border border-white/5 space-y-3">
          <div class="flex items-start gap-3">
            <div class="w-6 h-6 rounded-full bg-meet-blue/20 text-meet-blue text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
              2
            </div>
            <div class="text-xs text-gray-300">
              <p class="font-medium text-white mb-1">Set Permissions to "Allow"</p>
              <p>In the dropdown popup, switch <strong class="text-white">Microphone</strong> and <strong class="text-white">Camera</strong> to <span class="text-meet-green font-semibold">Allow</span>.</p>
              <div class="mt-2.5 flex items-center gap-3">
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-[#1e1f22] rounded-md border border-meet-border text-[11px]">
                  <Mic :size="12" class="text-meet-primary" />
                  <span>Microphone: <span class="text-emerald-400 font-semibold">Allow</span></span>
                </div>
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-[#1e1f22] rounded-md border border-meet-border text-[11px]">
                  <Video :size="12" class="text-meet-primary" />
                  <span>Camera: <span class="text-emerald-400 font-semibold">Allow</span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Visual Step 3: Retry -->
        <div class="p-3.5 rounded-xl bg-[#28292c] border border-white/5 space-y-3">
          <div class="flex items-start gap-3">
            <div class="w-6 h-6 rounded-full bg-meet-blue/20 text-meet-blue text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
              3
            </div>
            <div class="text-xs text-gray-300">
              <p class="font-medium text-white mb-1">Click "Try Again" below</p>
              <p>Once allowed in your browser settings, click the button below to activate your devices.</p>
            </div>
          </div>
        </div>

        <!-- Error Detail Banner if present -->
        <div v-if="errorDetail" class="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-xs flex items-center gap-2">
          <AlertCircle :size="15" class="shrink-0 text-red-400" />
          <span>{{ errorDetail }}</span>
        </div>
      </div>

      <!-- Footer Buttons -->
      <div class="px-6 py-4 border-t border-meet-border bg-[#1a1b1e] flex items-center justify-between gap-3">
        <button
          @click="close"
          class="px-4 py-2 text-xs font-medium text-meet-textMuted hover:text-white transition-colors"
        >
          Dismiss
        </button>

        <button
          @click="handleRetry"
          :disabled="isRetrying"
          class="px-6 py-2.5 bg-meet-blue hover:bg-meet-blue-hover disabled:opacity-50 text-white text-xs font-semibold rounded-full shadow-lg transition-all flex items-center gap-2"
        >
          <RefreshCw v-if="isRetrying" :size="14" class="animate-spin" />
          <span>{{ isRetrying ? 'Checking...' : 'Try Again' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Lock, X, Mic, Video, AlertCircle, RefreshCw } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/devices'

const props = withDefaults(
  defineProps<{
    isOpen: boolean
    kind?: 'microphone' | 'camera' | 'both'
    customError?: string
  }>(),
  {
    isOpen: false,
    kind: 'both',
    customError: '',
  }
)

const emit = defineEmits(['close', 'retry-success'])

const deviceStore = useDeviceStore()
const isRetrying = ref(false)

const title = computed(() => {
  if (props.kind === 'microphone') return 'Allow Microphone Access'
  if (props.kind === 'camera') return 'Allow Camera Access'
  return 'Allow Microphone & Camera Access'
})

const targetDeviceText = computed(() => {
  if (props.kind === 'microphone') return 'microphone'
  if (props.kind === 'camera') return 'camera'
  return 'microphone and camera'
})

const errorDetail = computed(() => {
  if (props.customError) return props.customError
  if (props.kind === 'microphone') return deviceStore.micError?.message
  if (props.kind === 'camera') return deviceStore.camError?.message
  return deviceStore.micError?.message || deviceStore.camError?.message || ''
})

function close() {
  emit('close')
}

async function handleRetry() {
  isRetrying.value = true
  try {
    let success = false
    if (props.kind === 'microphone' || props.kind === 'both') {
      try {
        await deviceStore.requestMicrophonePermission()
        success = true
      } catch {}
    }
    if (props.kind === 'camera' || props.kind === 'both') {
      try {
        await deviceStore.requestCameraPermission()
        success = true
      } catch {}
    }
    await deviceStore.enumerateDevices()
    if (success) {
      emit('retry-success')
      close()
    }
  } finally {
    isRetrying.value = false
  }
}
</script>
