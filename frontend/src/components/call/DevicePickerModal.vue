<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    @click.self="close"
  >
    <div class="w-full max-w-lg bg-[#202124] border border-meet-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-meet-border flex items-center justify-between bg-[#292a2d]">
        <h2 class="text-base font-semibold text-white">Audio & Video Settings</h2>
        <button
          @click="close"
          class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 space-y-5">
        <!-- Microphone Selection -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
              Microphone
            </label>
            <div class="flex items-center gap-1.5">
              <span
                v-if="deviceStore.micPermissionState === 'granted'"
                class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-medium"
              >
                Allowed
              </span>
              <button
                v-else
                @click="deviceStore.openPermissionGuide('microphone')"
                class="px-2 py-0.5 rounded-full bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 text-[10px] font-medium transition-colors"
              >
                Allow in Browser
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <Mic :size="18" class="text-meet-textMuted shrink-0" />
            <select
              v-model="deviceStore.selectedAudioInputId"
              @change="handleDeviceChange"
              class="w-full px-3 py-2 bg-[#303134] border border-meet-border rounded-lg text-sm text-white focus:border-meet-primary outline-none"
            >
              <option
                v-for="d in deviceStore.audioInputs"
                :key="d.deviceId"
                :value="d.deviceId"
              >
                {{ d.label || `Microphone (${d.deviceId.slice(0, 6)}...)` }}
              </option>
              <option v-if="deviceStore.audioInputs.length === 0" value="" disabled>
                No microphones found
              </option>
            </select>
          </div>
        </div>

        <!-- Speaker Selection & Test Tone -->
        <div class="space-y-2">
          <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
            Speakers / Audio Output
          </label>
          <div class="flex items-center gap-2">
            <Volume2 :size="18" class="text-meet-textMuted shrink-0" />
            <select
              v-model="deviceStore.selectedAudioOutputId"
              @change="handleDeviceChange"
              class="w-full px-3 py-2 bg-[#303134] border border-meet-border rounded-lg text-sm text-white focus:border-meet-primary outline-none"
            >
              <option
                v-for="d in deviceStore.audioOutputs"
                :key="d.deviceId"
                :value="d.deviceId"
              >
                {{ d.label || `Speaker (${d.deviceId.slice(0, 6)}...)` }}
              </option>
              <option v-if="deviceStore.audioOutputs.length === 0" value="">
                Default System Speaker
              </option>
            </select>
            <button
              @click="playTestTone"
              type="button"
              class="px-3 py-2 bg-meet-surfaceLight hover:bg-meet-border text-white text-xs font-medium rounded-lg shrink-0 transition-colors"
            >
              Test
            </button>
          </div>
        </div>

        <!-- Camera Selection -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
              Camera
            </label>
            <div class="flex items-center gap-1.5">
              <span
                v-if="deviceStore.camPermissionState === 'granted'"
                class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-medium"
              >
                Allowed
              </span>
              <button
                v-else
                @click="deviceStore.openPermissionGuide('camera')"
                class="px-2 py-0.5 rounded-full bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 text-[10px] font-medium transition-colors"
              >
                Allow in Browser
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <Video :size="18" class="text-meet-textMuted shrink-0" />
            <select
              v-model="deviceStore.selectedVideoInputId"
              @change="handleDeviceChange"
              class="w-full px-3 py-2 bg-[#303134] border border-meet-border rounded-lg text-sm text-white focus:border-meet-primary outline-none"
            >
              <option
                v-for="d in deviceStore.videoInputs"
                :key="d.deviceId"
                :value="d.deviceId"
              >
                {{ d.label || `Camera (${d.deviceId.slice(0, 6)}...)` }}
              </option>
              <option v-if="deviceStore.videoInputs.length === 0" value="" disabled>
                No cameras found
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-4 border-t border-meet-border bg-[#1a1b1e] flex justify-end">
        <button
          @click="close"
          class="px-5 py-2 bg-meet-blue hover:bg-meet-blue-hover text-white text-xs font-semibold rounded-full shadow-lg transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { X, Mic, Volume2, Video } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/devices'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits(['close', 'device-changed'])

const deviceStore = useDeviceStore()

function close() {
  emit('close')
}

function handleDeviceChange() {
  emit('device-changed')
}

function playTestTone() {
  try {
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime) // D5 note
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.5)
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.start()
    osc.stop(audioCtx.currentTime + 0.5)
  } catch (e) {
    console.warn('Audio test tone error:', e)
  }
}

onMounted(async () => {
  await deviceStore.enumerateDevices()
})
</script>
