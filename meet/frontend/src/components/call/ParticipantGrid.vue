<template>
  <div class="relative w-full h-full p-3 flex flex-col justify-center items-center overflow-hidden">
    <!-- Screen Share or Spotlight Stage Layout -->
    <div
      v-if="spotlightParticipant || activeScreenShareParticipant"
      class="w-full h-full flex flex-col md:flex-row gap-3 overflow-hidden"
    >
      <!-- Main Stage -->
      <div class="flex-1 h-full min-h-0 min-w-0">
        <VideoTile
          :participant="activeScreenShareParticipant ? activeScreenShareParticipant.participant : spotlightParticipant?.participant"
          :is-local="activeScreenShareParticipant ? activeScreenShareParticipant.isLocal : spotlightParticipant?.isLocal"
          :is-screen-share="!!activeScreenShareParticipant"
          :custom-display-name="activeScreenShareParticipant ? activeScreenShareParticipant.name : spotlightParticipant?.name"
          :is-active-speaker="activeSpeakerIdentity === (activeScreenShareParticipant?.identity || spotlightParticipant?.identity)"
          :is-hand-raised="meetingStore.raisedHands.has(activeScreenShareParticipant?.identity || spotlightParticipant?.identity || '')"
          :is-pinned="true"
          @toggle-pin="handleTogglePin(activeScreenShareParticipant?.identity || spotlightParticipant?.identity || '')"
        />
      </div>

      <!-- Filmstrip sidebar for other participants -->
      <div
        class="w-full md:w-64 h-32 md:h-full flex md:flex-col gap-2 overflow-x-auto md:overflow-y-auto shrink-0 pb-1"
      >
        <div
          v-for="item in filmstripParticipants"
          :key="item.identity"
          class="w-44 md:w-full h-full md:h-36 shrink-0"
        >
          <VideoTile
            :participant="item.participant"
            :is-local="item.isLocal"
            :custom-display-name="item.name"
            :is-active-speaker="activeSpeakerIdentity === item.identity"
            :is-hand-raised="meetingStore.raisedHands.has(item.identity)"
            :is-pinned="meetingStore.pinnedParticipantId === item.identity"
            @toggle-pin="handleTogglePin(item.identity)"
          />
        </div>
      </div>
    </div>

    <!-- Normal Dynamic Grid Layout -->
    <div
      v-else
      class="w-full h-full grid gap-3 place-items-stretch"
      :class="gridClass"
    >
      <div
        v-for="item in allGridParticipants"
        :key="item.identity"
        class="min-h-0 min-w-0 w-full h-full flex items-center justify-center"
      >
        <VideoTile
          :participant="item.participant"
          :is-local="item.isLocal"
          :custom-display-name="item.name"
          :is-active-speaker="activeSpeakerIdentity === item.identity"
          :is-hand-raised="meetingStore.raisedHands.has(item.identity)"
          :is-pinned="false"
          :role="item.role"
          @toggle-pin="handleTogglePin(item.identity)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Participant as LKParticipant, LocalParticipant, RemoteParticipant } from 'livekit-client'
import { useMeetingStore } from '@/stores/meeting'
import VideoTile from '@/components/call/VideoTile.vue'

export interface GridItem {
  identity: string
  name: string
  isLocal: boolean
  participant: LKParticipant | LocalParticipant | RemoteParticipant | null | any
  role?: 'host' | 'co_host' | 'participant'
}

const props = defineProps<{
  localParticipant: LocalParticipant | LKParticipant | null | any
  remoteParticipants: (RemoteParticipant | LKParticipant | any)[]
  localName: string
  activeSpeakerIdentity?: string | null
}>()

const meetingStore = useMeetingStore()

const allGridParticipants = computed<GridItem[]>(() => {
  const items: GridItem[] = []

  // Local participant
  items.push({
    identity: props.localParticipant?.identity || 'local',
    name: props.localName,
    isLocal: true,
    participant: props.localParticipant,
    role: meetingStore.role,
  })

  // Remote participants
  props.remoteParticipants.forEach((p) => {
    // Find role from meeting store participants list if available
    const dbPart = meetingStore.participants.find((item) => item.guest_name === p.name || `user_${item.user_id}` === p.identity)
    items.push({
      identity: p.identity,
      name: p.name || p.identity,
      isLocal: false,
      participant: p,
      role: dbPart?.role || 'participant',
    })
  })

  return items
})

const activeScreenShareParticipant = computed<GridItem | null>(() => {
  if (props.localParticipant?.isScreenShareEnabled) {
    return {
      identity: props.localParticipant.identity,
      name: props.localName,
      isLocal: true,
      participant: props.localParticipant,
    }
  }
  const sharingRemote = props.remoteParticipants.find((p) => p.isScreenShareEnabled)
  if (sharingRemote) {
    return {
      identity: sharingRemote.identity,
      name: sharingRemote.name || sharingRemote.identity,
      isLocal: false,
      participant: sharingRemote,
    }
  }
  return null
})

const spotlightParticipant = computed<GridItem | null>(() => {
  if (!meetingStore.pinnedParticipantId) return null
  return allGridParticipants.value.find((p) => p.identity === meetingStore.pinnedParticipantId) || null
})

const filmstripParticipants = computed<GridItem[]>(() => {
  const spotlightId = activeScreenShareParticipant.value?.identity || spotlightParticipant.value?.identity
  return allGridParticipants.value.filter((p) => p.identity !== spotlightId)
})

const gridClass = computed(() => {
  const count = allGridParticipants.value.length
  if (count <= 1) return 'grid-cols-1 max-w-4xl max-h-[85vh] mx-auto aspect-video'
  if (count === 2) return 'grid-cols-1 md:grid-cols-2 max-w-6xl max-h-[85vh] mx-auto'
  if (count <= 4) return 'grid-cols-2 max-w-6xl max-h-[85vh] mx-auto'
  if (count <= 6) return 'grid-cols-2 md:grid-cols-3 max-w-7xl'
  if (count <= 9) return 'grid-cols-3 max-w-7xl'
  return 'grid-cols-3 md:grid-cols-4 max-w-7xl'
})

function handleTogglePin(identity: string) {
  meetingStore.setPinned(identity)
}
</script>
