<template>
  <div class="w-full h-full flex flex-col bg-[#202124] border-l border-meet-border text-meet-text select-none">
    <!-- Header -->
    <div class="px-4 sm:px-5 py-4 border-b border-meet-border flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button
          @click="meetingStore.closePanel()"
          class="md:hidden p-1.5 rounded-full hover:bg-meet-surfaceLight text-white mr-1"
          title="Back to call"
        >
          <ArrowLeft :size="20" />
        </button>
        <ShieldCheck :size="20" class="text-meet-primary" />
        <h2 class="text-lg font-medium text-white">Host controls</h2>
      </div>
      <button
        @click="meetingStore.closePanel()"
        class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
        title="Close"
      >
        <X :size="20" />
      </button>
    </div>

    <div class="p-5 space-y-6 flex-1 overflow-y-auto">
      <!-- Meeting Management Section -->
      <div class="space-y-4">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
          Meeting access
        </h3>

        <!-- Lobby Toggle -->
        <div class="flex items-start justify-between gap-4 p-3 bg-[#303134] rounded-xl">
          <div class="space-y-0.5">
            <label class="text-sm font-medium text-white cursor-pointer" for="toggle-lobby">
              Waiting room (Lobby)
            </label>
            <p class="text-xs text-meet-textMuted">
              When turned on, everyone must ask to join and be admitted by the host.
            </p>
          </div>
          <input
            id="toggle-lobby"
            type="checkbox"
            :checked="meetingStore.currentMeeting?.lobby_enabled"
            @change="handleToggleLobby"
            class="mt-1 w-5 h-5 accent-meet-blue cursor-pointer"
          />
        </div>

        <!-- Lock Meeting Toggle -->
        <div class="flex items-start justify-between gap-4 p-3 bg-[#303134] rounded-xl">
          <div class="space-y-0.5">
            <label class="text-sm font-medium text-white cursor-pointer" for="toggle-lock">
              Lock meeting
            </label>
            <p class="text-xs text-meet-textMuted">
              Block all new participants from joining, even with the meeting link.
            </p>
          </div>
          <input
            id="toggle-lock"
            type="checkbox"
            :checked="meetingStore.currentMeeting?.is_locked"
            @change="handleToggleLock"
            class="mt-1 w-5 h-5 accent-meet-blue cursor-pointer"
          />
        </div>
      </div>

      <!-- End Call for Everyone Section -->
      <div class="pt-4 border-t border-meet-border space-y-3">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-meet-red">
          Danger Zone
        </h3>
        <p class="text-xs text-meet-textMuted">
          Ending the call will instantly disconnect all participants and close the room.
        </p>
        <button
          @click="handleEndForAll"
          class="w-full py-2.5 px-4 bg-meet-red hover:bg-meet-redHover text-white rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2 shadow"
        >
          <PhoneOff :size="16" />
          <span>End meeting for all</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ShieldCheck, X, PhoneOff, ArrowLeft } from 'lucide-vue-next'
import { useMeetingStore } from '@/stores/meeting'
import { livekitManager } from '@/lib/livekit'

const emit = defineEmits(['end-for-all'])
const meetingStore = useMeetingStore()

async function handleToggleLobby(e: Event) {
  const target = e.target as HTMLInputElement
  if (!meetingStore.currentMeeting) return
  await meetingStore.updateSettings(meetingStore.currentMeeting.code, {
    lobby_enabled: target.checked,
  })
}

async function handleToggleLock(e: Event) {
  const target = e.target as HTMLInputElement
  if (!meetingStore.currentMeeting) return
  await meetingStore.updateSettings(meetingStore.currentMeeting.code, {
    is_locked: target.checked,
  })
}

async function handleEndForAll() {
  if (confirm('Are you sure you want to end this meeting for everyone?')) {
    if (meetingStore.currentMeeting) {
      await meetingStore.endMeetingForAll(meetingStore.currentMeeting.code)
      await livekitManager.sendData({
        type: 'meeting_ended',
      })
    }
    emit('end-for-all')
  }
}
</script>
