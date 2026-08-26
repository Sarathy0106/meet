import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDeviceStore = defineStore('devices', () => {
  const isAudioEnabled = ref<boolean>(true)
  const isVideoEnabled = ref<boolean>(true)
  const isScreenSharing = ref<boolean>(false)

  const audioInputs = ref<MediaDeviceInfo[]>([])
  const audioOutputs = ref<MediaDeviceInfo[]>([])
  const videoInputs = ref<MediaDeviceInfo[]>([])

  const selectedAudioInputId = ref<string>('')
  const selectedAudioOutputId = ref<string>('')
  const selectedVideoInputId = ref<string>('')

  const localPreviewStream = ref<MediaStream | null>(null)
  const audioLevel = ref<number>(0)

  async function enumerateDevices() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        return
      }
      const devices = await navigator.mediaDevices.enumerateDevices()
      audioInputs.value = devices.filter((d) => d.kind === 'audioinput')
      audioOutputs.value = devices.filter((d) => d.kind === 'audiooutput')
      videoInputs.value = devices.filter((d) => d.kind === 'videoinput')

      if (audioInputs.value.length && !selectedAudioInputId.value) {
        selectedAudioInputId.value = audioInputs.value[0].deviceId
      }
      if (audioOutputs.value.length && !selectedAudioOutputId.value) {
        selectedAudioOutputId.value = audioOutputs.value[0].deviceId
      }
      if (videoInputs.value.length && !selectedVideoInputId.value) {
        selectedVideoInputId.value = videoInputs.value[0].deviceId
      }
    } catch (e) {
      console.warn('Failed to enumerate devices:', e)
    }
  }

  async function startPreviewStream() {
    stopPreviewStream()
    try {
      const constraints: MediaStreamConstraints = {
        audio: isAudioEnabled.value
          ? selectedAudioInputId.value
            ? { deviceId: { exact: selectedAudioInputId.value } }
            : true
          : false,
        video: isVideoEnabled.value
          ? selectedVideoInputId.value
            ? { deviceId: { exact: selectedVideoInputId.value }, width: { ideal: 1280 }, height: { ideal: 720 } }
            : { width: { ideal: 1280 }, height: { ideal: 720 } }
          : false,
      }

      if (isAudioEnabled.value || isVideoEnabled.value) {
        const stream = await navigator.mediaDevices.getUserMedia(constraints)
        localPreviewStream.value = stream
        await enumerateDevices()
      }
    } catch (err) {
      console.warn('Error starting preview stream:', err)
    }
  }

  function stopPreviewStream() {
    if (localPreviewStream.value) {
      localPreviewStream.value.getTracks().forEach((track) => track.stop())
      localPreviewStream.value = null
    }
  }

  function toggleAudio() {
    isAudioEnabled.value = !isAudioEnabled.value
    if (localPreviewStream.value) {
      localPreviewStream.value.getAudioTracks().forEach((track) => {
        track.enabled = isAudioEnabled.value
      })
    }
  }

  function toggleVideo() {
    isVideoEnabled.value = !isVideoEnabled.value
    if (localPreviewStream.value) {
      localPreviewStream.value.getVideoTracks().forEach((track) => {
        track.enabled = isVideoEnabled.value
      })
    }
  }

  return {
    isAudioEnabled,
    isVideoEnabled,
    isScreenSharing,
    audioInputs,
    audioOutputs,
    videoInputs,
    selectedAudioInputId,
    selectedAudioOutputId,
    selectedVideoInputId,
    localPreviewStream,
    audioLevel,
    enumerateDevices,
    startPreviewStream,
    stopPreviewStream,
    toggleAudio,
    toggleVideo,
  }
})
