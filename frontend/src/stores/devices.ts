import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type PermissionState,
  type ParsedMediaError,
  parseMediaError,
  queryPermissionState,
  listenToPermissionChanges,
} from '@/lib/permissions'

export const useDeviceStore = defineStore('devices', () => {
  const isAudioEnabled = ref<boolean>(true)
  const isVideoEnabled = ref<boolean>(true)
  const isScreenSharing = ref<boolean>(false)

  // Permissions state
  const micPermissionState = ref<PermissionState>('prompt')
  const camPermissionState = ref<PermissionState>('prompt')
  const micError = ref<ParsedMediaError | null>(null)
  const camError = ref<ParsedMediaError | null>(null)

  // Permission guidance modal state
  const isPermissionGuideOpen = ref<boolean>(false)
  const activePermissionGuideKind = ref<'microphone' | 'camera' | 'both'>('both')

  // Available devices
  const audioInputs = ref<MediaDeviceInfo[]>([])
  const audioOutputs = ref<MediaDeviceInfo[]>([])
  const videoInputs = ref<MediaDeviceInfo[]>([])

  // Selected device IDs
  const selectedAudioInputId = ref<string>('')
  const selectedAudioOutputId = ref<string>('')
  const selectedVideoInputId = ref<string>('')

  // Local media stream & audio level
  const localPreviewStream = ref<MediaStream | null>(null)
  const audioLevel = ref<number>(0)
  let audioContext: AudioContext | null = null
  let analyser: AnalyserNode | null = null
  let animFrameId: number | null = null

  let permissionCleanups: (() => void)[] = []
  let isListenersInitialized = false

  function openPermissionGuide(kind: 'microphone' | 'camera' | 'both' = 'both') {
    activePermissionGuideKind.value = kind
    isPermissionGuideOpen.value = true
  }

  function closePermissionGuide() {
    isPermissionGuideOpen.value = false
  }

  async function updatePermissionStates() {
    micPermissionState.value = await queryPermissionState('microphone')
    camPermissionState.value = await queryPermissionState('camera')
  }

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

  function setupAudioMeter(stream: MediaStream) {
    stopAudioMeter()
    const audioTrack = stream.getAudioTracks()[0]
    if (!audioTrack) return

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      if (!AudioCtx) return
      audioContext = new AudioCtx()
      if (audioContext.state === 'suspended') {
        audioContext.resume()
      }
      const source = audioContext.createMediaStreamSource(stream)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      const checkVolume = () => {
        if (!analyser) return
        analyser.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i]
        }
        const average = sum / bufferLength
        audioLevel.value = Math.min(100, Math.round((average / 128) * 100))
        animFrameId = requestAnimationFrame(checkVolume)
      }
      checkVolume()
    } catch (e) {
      console.warn('Could not initialize audio meter:', e)
    }
  }

  function stopAudioMeter() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId)
      animFrameId = null
    }
    if (audioContext) {
      try {
        audioContext.close()
      } catch {}
      audioContext = null
      analyser = null
    }
    audioLevel.value = 0
  }

  /**
   * Starts local preview stream for PreJoinView with full error isolation.
   * If audio or video individually fails, the other can still succeed.
   */
  async function startPreviewStream() {
    stopPreviewStream()
    await updatePermissionStates()

    const newStream = new MediaStream()

    // 1. Request Audio Track if enabled
    if (isAudioEnabled.value) {
      try {
        const audioConstraints: boolean | MediaTrackConstraints = selectedAudioInputId.value
          ? { deviceId: { exact: selectedAudioInputId.value } }
          : true

        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints, video: false })
        const audioTrack = audioStream.getAudioTracks()[0]
        if (audioTrack) {
          newStream.addTrack(audioTrack)
          micPermissionState.value = 'granted'
          micError.value = null
        }
      } catch (err: any) {
        console.warn('Preview Audio error:', err)
        const parsed = parseMediaError('microphone', err)
        micError.value = parsed
        if (parsed.isBlockedByBrowser) {
          micPermissionState.value = 'denied'
        }
        isAudioEnabled.value = false
      }
    }

    // 2. Request Video Track if enabled
    if (isVideoEnabled.value) {
      try {
        const videoConstraints: MediaTrackConstraints = selectedVideoInputId.value
          ? { deviceId: { exact: selectedVideoInputId.value }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { width: { ideal: 1280 }, height: { ideal: 720 } }

        const videoStream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints, audio: false })
        const videoTrack = videoStream.getVideoTracks()[0]
        if (videoTrack) {
          newStream.addTrack(videoTrack)
          camPermissionState.value = 'granted'
          camError.value = null
        }
      } catch (err: any) {
        console.warn('Preview Video error:', err)
        const parsed = parseMediaError('camera', err)
        camError.value = parsed
        if (parsed.isBlockedByBrowser) {
          camPermissionState.value = 'denied'
        }
        isVideoEnabled.value = false
      }
    }

    if (newStream.getTracks().length > 0) {
      localPreviewStream.value = newStream
      setupAudioMeter(newStream)
      await enumerateDevices()
    } else {
      localPreviewStream.value = null
    }

    initDeviceListeners()
  }

  function stopPreviewStream() {
    stopAudioMeter()
    if (localPreviewStream.value) {
      localPreviewStream.value.getTracks().forEach((track) => {
        try {
          track.stop()
        } catch {}
      })
      localPreviewStream.value = null
    }
  }

  /**
   * Explicitly requests microphone permission and acquires audio track.
   */
  async function requestMicrophonePermission(): Promise<boolean> {
    try {
      const audioConstraints: boolean | MediaTrackConstraints = selectedAudioInputId.value
        ? { deviceId: { exact: selectedAudioInputId.value } }
        : true

      const stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints, video: false })
      const newAudioTrack = stream.getAudioTracks()[0]

      if (newAudioTrack) {
        micPermissionState.value = 'granted'
        micError.value = null
        isAudioEnabled.value = true

        if (!localPreviewStream.value) {
          localPreviewStream.value = new MediaStream([newAudioTrack])
        } else {
          // Remove old audio tracks if any
          localPreviewStream.value.getAudioTracks().forEach((t) => {
            t.stop()
            localPreviewStream.value?.removeTrack(t)
          })
          localPreviewStream.value.addTrack(newAudioTrack)
        }
        setupAudioMeter(localPreviewStream.value)
        await enumerateDevices()
        return true
      }
      return false
    } catch (err: any) {
      const parsed = parseMediaError('microphone', err)
      micError.value = parsed
      if (parsed.isBlockedByBrowser) {
        micPermissionState.value = 'denied'
      }
      isAudioEnabled.value = false
      throw err
    }
  }

  /**
   * Explicitly requests camera permission and acquires video track.
   */
  async function requestCameraPermission(): Promise<boolean> {
    try {
      const videoConstraints: MediaTrackConstraints = selectedVideoInputId.value
        ? { deviceId: { exact: selectedVideoInputId.value }, width: { ideal: 1280 }, height: { ideal: 720 } }
        : { width: { ideal: 1280 }, height: { ideal: 720 } }

      const stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints, audio: false })
      const newVideoTrack = stream.getVideoTracks()[0]

      if (newVideoTrack) {
        camPermissionState.value = 'granted'
        camError.value = null
        isVideoEnabled.value = true

        if (!localPreviewStream.value) {
          localPreviewStream.value = new MediaStream([newVideoTrack])
        } else {
          localPreviewStream.value.getVideoTracks().forEach((t) => {
            t.stop()
            localPreviewStream.value?.removeTrack(t)
          })
          localPreviewStream.value.addTrack(newVideoTrack)
        }
        await enumerateDevices()
        return true
      }
      return false
    } catch (err: any) {
      const parsed = parseMediaError('camera', err)
      camError.value = parsed
      if (parsed.isBlockedByBrowser) {
        camPermissionState.value = 'denied'
      }
      isVideoEnabled.value = false
      throw err
    }
  }

  async function toggleAudio() {
    if (isAudioEnabled.value) {
      // Mute audio
      isAudioEnabled.value = false
      if (localPreviewStream.value) {
        localPreviewStream.value.getAudioTracks().forEach((track) => {
          track.enabled = false
        })
      }
      stopAudioMeter()
    } else {
      // Unmute / enable audio
      const existingTrack = localPreviewStream.value?.getAudioTracks()[0]
      if (existingTrack && existingTrack.readyState === 'live') {
        existingTrack.enabled = true
        isAudioEnabled.value = true
        micError.value = null
        if (localPreviewStream.value) {
          setupAudioMeter(localPreviewStream.value)
        }
      } else {
        // Need to acquire new audio track / request permission
        await requestMicrophonePermission()
      }
    }
  }

  async function toggleVideo() {
    if (isVideoEnabled.value) {
      // Turn off camera
      isVideoEnabled.value = false
      if (localPreviewStream.value) {
        localPreviewStream.value.getVideoTracks().forEach((track) => {
          track.enabled = false
        })
      }
    } else {
      // Turn on camera
      const existingTrack = localPreviewStream.value?.getVideoTracks()[0]
      if (existingTrack && existingTrack.readyState === 'live') {
        existingTrack.enabled = true
        isVideoEnabled.value = true
        camError.value = null
      } else {
        // Need to acquire new video track / request permission
        await requestCameraPermission()
      }
    }
  }

  function initDeviceListeners() {
    if (isListenersInitialized || typeof window === 'undefined') return
    isListenersInitialized = true

    // Device plugged / unplugged listener
    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      const handleDeviceChange = async () => {
        console.log('Media devices changed, re-enumerating...')
        await enumerateDevices()
      }
      navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange)
      permissionCleanups.push(() => {
        navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange)
      })
    }

    // Permission change listeners
    permissionCleanups.push(
      listenToPermissionChanges('microphone', async (state) => {
        micPermissionState.value = state
        if (state === 'granted') {
          micError.value = null
          await enumerateDevices()
        }
      })
    )

    permissionCleanups.push(
      listenToPermissionChanges('camera', async (state) => {
        camPermissionState.value = state
        if (state === 'granted') {
          camError.value = null
          await enumerateDevices()
        }
      })
    )
  }

  function cleanupListeners() {
    permissionCleanups.forEach((c) => c())
    permissionCleanups = []
    isListenersInitialized = false
  }

  return {
    isAudioEnabled,
    isVideoEnabled,
    isScreenSharing,
    micPermissionState,
    camPermissionState,
    micError,
    camError,
    isPermissionGuideOpen,
    activePermissionGuideKind,
    audioInputs,
    audioOutputs,
    videoInputs,
    selectedAudioInputId,
    selectedAudioOutputId,
    selectedVideoInputId,
    localPreviewStream,
    audioLevel,
    openPermissionGuide,
    closePermissionGuide,
    enumerateDevices,
    startPreviewStream,
    stopPreviewStream,
    requestMicrophonePermission,
    requestCameraPermission,
    toggleAudio,
    toggleVideo,
    initDeviceListeners,
    cleanupListeners,
  }
})
