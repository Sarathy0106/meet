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
        <h2 class="text-lg font-medium text-white">People</h2>
      </div>
      <button
        @click="meetingStore.closePanel()"
        class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
        title="Close"
      >
        <X :size="20" />
      </button>
    </div>

    <!-- Search Input -->
    <div class="px-4 py-3">
      <div class="relative">
        <Search :size="16" class="absolute left-3.5 top-3 text-meet-textMuted" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search for people"
          class="w-full pl-10 pr-4 py-2 bg-[#303134] border border-transparent focus:border-meet-primary rounded-full text-sm text-white placeholder-meet-textMuted outline-none transition-colors"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-4 py-2 space-y-6">
      <!-- Waiting Room / Lobby Section (Host only) -->
      <div v-if="meetingStore.isHost && meetingStore.waitingParticipants.length > 0" class="space-y-2">
        <div class="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-meet-yellow">
          <span>Waiting in lobby ({{ meetingStore.waitingParticipants.length }})</span>
          <button
            @click="admitAll"
            class="text-meet-primary hover:underline text-xs capitalize font-medium"
          >
            Admit all
          </button>
        </div>

        <div class="space-y-1.5 bg-[#303134]/60 p-2.5 rounded-xl border border-yellow-500/20">
          <div
            v-for="waiter in meetingStore.waitingParticipants"
            :key="waiter.id"
            class="flex items-center justify-between py-1.5 px-2 rounded-lg bg-[#202124]"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <AvatarInitials :name="waiter.display_name" size="sm" />
              <span class="text-sm text-white truncate">{{ waiter.display_name }}</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button
                @click="admitOne(waiter.id, true)"
                class="px-2.5 py-1 bg-meet-blue hover:bg-meet-blue-hover text-white text-xs font-medium rounded-full transition-colors"
              >
                Admit
              </button>
              <button
                @click="admitOne(waiter.id, false)"
                class="px-2.5 py-1 hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white text-xs rounded-full transition-colors"
              >
                Deny
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- In the meeting Section -->
      <div class="space-y-3">
        <div class="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-meet-textMuted">
          <span>In call ({{ filteredParticipants.length }})</span>
          <button
            v-if="meetingStore.isHost && filteredParticipants.length > 1"
            @click="muteAll"
            class="text-xs text-meet-primary hover:underline font-medium normal-case"
          >
            Mute all
          </button>
        </div>

        <div class="space-y-1">
          <div
            v-for="p in filteredParticipants"
            :key="p.identity"
            class="flex items-center justify-between py-2 px-2.5 rounded-lg hover:bg-[#303134] transition-colors group"
          >
            <div class="flex items-center gap-3 min-w-0">
              <AvatarInitials :name="p.name" size="md" />
              <div class="flex flex-col min-w-0">
                <div class="flex items-center gap-1.5 truncate">
                  <span class="text-sm font-medium text-white truncate">{{ p.name }}</span>
                  <span v-if="p.isLocal" class="text-xs text-meet-textMuted font-normal">(You)</span>
                  <span
                    v-if="p.role === 'host'"
                    class="px-1.5 py-0.2 bg-blue-500/20 text-blue-300 text-[10px] uppercase font-semibold rounded"
                  >
                    Host
                  </span>
                </div>
                <span v-if="meetingStore.raisedHands.has(p.identity)" class="text-xs text-meet-yellow font-medium">
                  ✋ Hand raised
                </span>
              </div>
            </div>

            <!-- Right icons / Host controls -->
            <div class="flex items-center gap-2 shrink-0">
              <!-- Hand raise indicator -->
              <span v-if="meetingStore.raisedHands.has(p.identity)" class="text-meet-yellow text-sm animate-bounce">
                ✋
              </span>

              <!-- Pin / Spotlight -->
              <button
                @click="handleTogglePin(p.identity)"
                class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors opacity-0 group-hover:opacity-100"
                :title="meetingStore.pinnedParticipantId === p.identity ? 'Unpin' : 'Pin'"
              >
                <Pin :size="15" :class="{ 'text-meet-primary fill-meet-primary': meetingStore.pinnedParticipantId === p.identity }" />
              </button>

              <!-- Mute / Mic Status -->
              <div class="p-1 text-meet-textMuted">
                <MicOff v-if="!p.isAudioActive" :size="16" class="text-meet-red" />
                <Mic v-else :size="16" class="text-meet-green" />
              </div>

              <!-- Host actions menu for remote participant -->
              <div v-if="meetingStore.isHost && !p.isLocal" class="relative">
                <button
                  @click="toggleDropdown(p.identity)"
                  class="p-1.5 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
                >
                  <MoreVertical :size="16" />
                </button>

                <!-- Actions dropdown -->
                <div
                  v-if="activeDropdownIdentity === p.identity"
                  class="absolute right-0 top-8 w-44 bg-[#303134] border border-meet-border rounded-lg shadow-xl py-1 z-30"
                >
                  <button
                    @click="remoteMute(p.identity)"
                    class="w-full px-4 py-2 text-left text-xs hover:bg-meet-surfaceLight text-meet-text hover:text-white flex items-center gap-2"
                  >
                    <MicOff :size="14" class="text-meet-red" />
                    <span>Mute participant</span>
                  </button>
                  <button
                    @click="kickParticipant(p.identity)"
                    class="w-full px-4 py-2 text-left text-xs hover:bg-meet-surfaceLight text-meet-red hover:text-red-400 flex items-center gap-2"
                  >
                    <UserX :size="14" />
                    <span>Remove from call</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Search, Pin, Mic, MicOff, MoreVertical, UserX, ArrowLeft } from 'lucide-vue-next'
import { useMeetingStore } from '@/stores/meeting'
import { livekitManager } from '@/lib/livekit'
import AvatarInitials from '@/components/common/AvatarInitials.vue'

const props = defineProps<{
  localName: string
}>()

const meetingStore = useMeetingStore()
const searchQuery = ref('')
const activeDropdownIdentity = ref<string | null>(null)

interface DisplayParticipant {
  identity: string
  name: string
  isLocal: boolean
  role: 'host' | 'co_host' | 'participant'
  isAudioActive: boolean
}

const allParticipants = computed<DisplayParticipant[]>(() => {
  const list: DisplayParticipant[] = []
  const lkRoom = livekitManager.currentRoom

  // Local
  list.push({
    identity: lkRoom?.localParticipant?.identity || 'local',
    name: props.localName,
    isLocal: true,
    role: meetingStore.role,
    isAudioActive: lkRoom?.localParticipant?.isMicrophoneEnabled ?? true,
  })

  // Remote
  if (lkRoom) {
    lkRoom.remoteParticipants.forEach((p) => {
      const dbPart = meetingStore.participants.find((item) => item.guest_name === p.name || `user_${item.user_id}` === p.identity)
      list.push({
        identity: p.identity,
        name: p.name || p.identity,
        isLocal: false,
        role: dbPart?.role || 'participant',
        isAudioActive: p.isMicrophoneEnabled,
      })
    })
  }

  return list
})

const filteredParticipants = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return allParticipants.value
  return allParticipants.value.filter((p) => p.name.toLowerCase().includes(q))
})

function handleTogglePin(identity: string) {
  meetingStore.setPinned(identity)
}

function toggleDropdown(identity: string) {
  if (activeDropdownIdentity.value === identity) {
    activeDropdownIdentity.value = null
  } else {
    activeDropdownIdentity.value = identity
  }
}

async function admitOne(participantId: string, admit: boolean) {
  if (meetingStore.currentMeeting) {
    await meetingStore.admitParticipant(meetingStore.currentMeeting.code, participantId, admit)
  }
}

async function admitAll() {
  if (!meetingStore.currentMeeting) return
  const waiters = [...meetingStore.waitingParticipants]
  for (const w of waiters) {
    await meetingStore.admitParticipant(meetingStore.currentMeeting.code, w.id, true)
  }
}

async function remoteMute(targetIdentity: string) {
  activeDropdownIdentity.value = null
  await livekitManager.sendData({
    type: 'mute_participant',
    targetId: targetIdentity,
  })
}

async function kickParticipant(targetIdentity: string) {
  activeDropdownIdentity.value = null
  await livekitManager.sendData({
    type: 'kick_participant',
    targetId: targetIdentity,
  })
}

async function muteAll() {
  await livekitManager.sendData({
    type: 'mute_participant',
    targetId: '*', // wildcard for all
  })
}
</script>
