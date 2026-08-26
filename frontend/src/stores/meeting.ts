import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { Meeting, Participant } from '@/types'

export const useMeetingStore = defineStore('meeting', () => {
  const currentMeeting = ref<Meeting | null>(null)
  const currentParticipantId = ref<string | null>(null)
  const role = ref<'host' | 'co_host' | 'participant'>('participant')
  const participantStatus = ref<'waiting' | 'admitted' | 'rejected' | 'left'>('admitted')
  
  const participants = ref<Participant[]>([])
  const waitingParticipants = ref<Participant[]>([])
  
  const raisedHands = ref<Set<string>>(new Set())
  const pinnedParticipantId = ref<string | null>(null)
  const activeSpeakerId = ref<string | null>(null)
  
  const activePanel = ref<'chat' | 'people' | 'host_controls' | null>(null)
  const isDeviceModalOpen = ref<boolean>(false)
  const isHostControlsOpen = ref<boolean>(false)

  const isHost = computed(() => role.value === 'host' || role.value === 'co_host')
  const isMeetingEnded = computed(() => !!currentMeeting.value?.ended_at)

  function setMeeting(meeting: Meeting, pId?: string, userRole?: 'host' | 'co_host' | 'participant', status?: 'waiting' | 'admitted' | 'rejected' | 'left') {
    currentMeeting.value = meeting
    if (pId) currentParticipantId.value = pId
    if (userRole) role.value = userRole
    if (status) participantStatus.value = status
  }

  function togglePanel(panel: 'chat' | 'people' | 'host_controls') {
    if (activePanel.value === panel) {
      activePanel.value = null
    } else {
      activePanel.value = panel
    }
  }

  function closePanel() {
    activePanel.value = null
  }

  function setPinned(id: string | null) {
    if (pinnedParticipantId.value === id) {
      pinnedParticipantId.value = null
    } else {
      pinnedParticipantId.value = id
    }
  }

  function toggleHandRaise(identity: string) {
    if (raisedHands.value.has(identity)) {
      raisedHands.value.delete(identity)
    } else {
      raisedHands.value.add(identity)
    }
  }

  function setHandRaise(identity: string, isRaised: boolean) {
    if (isRaised) {
      raisedHands.value.add(identity)
    } else {
      raisedHands.value.delete(identity)
    }
  }

  async function fetchMeeting(code: string) {
    const res = await api.get(`/meetings/${code}`)
    currentMeeting.value = res.data
    return res.data
  }

  async function fetchParticipants(code: string) {
    try {
      const res = await api.get(`/meetings/${code}/participants`)
      const list: Participant[] = res.data
      participants.value = list.filter((p) => p.status === 'admitted' && !p.left_at)
      waitingParticipants.value = list.filter((p) => p.status === 'waiting')
    } catch (e) {
      console.warn('Failed to fetch participants list:', e)
    }
  }

  async function admitParticipant(code: string, participantId: string, admit: boolean) {
    try {
      await api.post(`/meetings/${code}/admit`, {
        participant_id: participantId,
        admit,
      })
      await fetchParticipants(code)
    } catch (e) {
      console.warn('Failed to admit participant:', e)
    }
  }

  async function updateSettings(code: string, settings: { lobby_enabled?: boolean; is_locked?: boolean; title?: string }) {
    try {
      const res = await api.patch(`/meetings/${code}/settings`, settings)
      currentMeeting.value = res.data
      return res.data
    } catch (e) {
      console.warn('Failed to update meeting settings:', e)
    }
  }

  async function endMeetingForAll(code: string) {
    try {
      await api.post(`/meetings/${code}/end`)
      if (currentMeeting.value) {
        currentMeeting.value.ended_at = new Date().toISOString()
      }
    } catch (e) {
      console.warn('Failed to end meeting:', e)
    }
  }

  async function leaveMeeting(code: string) {
    if (currentParticipantId.value) {
      try {
        await api.post(`/meetings/${code}/leave`, null, {
          params: { participant_id: currentParticipantId.value },
        })
      } catch (e) {
        console.warn('Failed to leave meeting API:', e)
      }
    }
  }

  function reset() {
    currentMeeting.value = null
    currentParticipantId.value = null
    role.value = 'participant'
    participantStatus.value = 'admitted'
    participants.value = []
    waitingParticipants.value = []
    raisedHands.value.clear()
    pinnedParticipantId.value = null
    activeSpeakerId.value = null
    activePanel.value = null
  }

  return {
    currentMeeting,
    currentParticipantId,
    role,
    participantStatus,
    participants,
    waitingParticipants,
    raisedHands,
    pinnedParticipantId,
    activeSpeakerId,
    activePanel,
    isDeviceModalOpen,
    isHostControlsOpen,
    isHost,
    isMeetingEnded,
    setMeeting,
    togglePanel,
    closePanel,
    setPinned,
    toggleHandRaise,
    setHandRaise,
    fetchMeeting,
    fetchParticipants,
    admitParticipant,
    updateSettings,
    endMeetingForAll,
    leaveMeeting,
    reset,
  }
})
