import {
  Room,
  RoomEvent,
  VideoPresets,
  RemoteParticipant,
  LocalParticipant,
  Participant as LKParticipant,
  Track,
} from 'livekit-client'
import type { DataPacket } from '@/types'

export class LiveKitManager {
  private room: Room | null = null
  private onDataReceivedCallbacks: ((packet: DataPacket, participant?: LKParticipant) => void)[] = []
  private onParticipantUpdateCallbacks: (() => void)[] = []
  private onActiveSpeakerChangeCallbacks: ((speakers: LKParticipant[]) => void)[] = []
  private onConnectionStatusChangeCallbacks: ((status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void)[] = []
  private onScreenShareStoppedCallbacks: (() => void)[] = []

  public get currentRoom(): Room | null {
    return this.room
  }

  public get localParticipant(): LocalParticipant | null {
    return this.room?.localParticipant || null
  }

  public get remoteParticipants(): RemoteParticipant[] {
    if (!this.room) return []
    return Array.from(this.room.remoteParticipants.values())
  }

  public async connect(url: string, token: string): Promise<Room> {
    this.disconnect()

    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
      videoCaptureDefaults: {
        resolution: VideoPresets.h720.resolution,
      },
    })

    this.room = room
    this.onConnectionStatusChangeCallbacks.forEach((cb) => cb('connecting'))

    // Setup Room Events
    room.on(RoomEvent.Connected, () => {
      this.onConnectionStatusChangeCallbacks.forEach((cb) => cb('connected'))
      this.notifyParticipantUpdate()

      // Handle browser autoplay policy
      if (!room.canPlaybackAudio) {
        room.startAudio().catch((e) => {
          console.warn('LiveKit startAudio auto-unlock deferred until user gesture:', e)
        })
      }
    })

    room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
      if (!room.canPlaybackAudio) {
        console.warn('Audio playback status: playback blocked by browser')
      }
    })

    room.on(RoomEvent.Reconnecting, () => {
      this.onConnectionStatusChangeCallbacks.forEach((cb) => cb('reconnecting'))
    })

    room.on(RoomEvent.Reconnected, () => {
      this.onConnectionStatusChangeCallbacks.forEach((cb) => cb('connected'))
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.Disconnected, () => {
      this.onConnectionStatusChangeCallbacks.forEach((cb) => cb('disconnected'))
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.ParticipantConnected, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.ParticipantDisconnected, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.TrackSubscribed, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.TrackUnsubscribed, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.TrackMuted, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.TrackUnmuted, () => {
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.LocalTrackUnpublished, (publication) => {
      if (publication.source === Track.Source.ScreenShare) {
        this.onScreenShareStoppedCallbacks.forEach((cb) => cb())
      }
      this.notifyParticipantUpdate()
    })

    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      this.onActiveSpeakerChangeCallbacks.forEach((cb) => cb(speakers))
    })

    room.on(RoomEvent.DataReceived, (payload: Uint8Array, participant?: RemoteParticipant) => {
      try {
        const text = new TextDecoder().decode(payload)
        const packet: DataPacket = JSON.parse(text)
        this.onDataReceivedCallbacks.forEach((cb) => cb(packet, participant))
      } catch (e) {
        console.warn('Failed to parse LiveKit data packet:', e)
      }
    })

    await room.connect(url, token)
    return room
  }

  public async setCameraEnabled(enabled: boolean, deviceId?: string): Promise<void> {
    if (!this.room || !this.room.localParticipant) return
    const options = deviceId ? { deviceId: { exact: deviceId } } : undefined
    await this.room.localParticipant.setCameraEnabled(enabled, options)
    this.notifyParticipantUpdate()
  }

  public async setMicrophoneEnabled(enabled: boolean, deviceId?: string): Promise<void> {
    if (!this.room || !this.room.localParticipant) return
    const options = deviceId ? { deviceId: { exact: deviceId } } : undefined
    await this.room.localParticipant.setMicrophoneEnabled(enabled, options)
    this.notifyParticipantUpdate()
  }

  public async setScreenShareEnabled(enabled: boolean): Promise<void> {
    if (!this.room || !this.room.localParticipant) return
    await this.room.localParticipant.setScreenShareEnabled(enabled)
    this.notifyParticipantUpdate()
  }

  public async switchAudioInput(deviceId: string): Promise<void> {
    if (!this.room) return
    await this.room.switchActiveDevice('audioinput', deviceId)
  }

  public async switchVideoInput(deviceId: string): Promise<void> {
    if (!this.room) return
    await this.room.switchActiveDevice('videoinput', deviceId)
  }

  public async switchAudioOutput(deviceId: string): Promise<void> {
    if (!this.room) return
    await this.room.switchActiveDevice('audiooutput', deviceId)
  }

  public async sendData(packet: DataPacket): Promise<void> {
    if (!this.room || !this.room.localParticipant) return
    const text = JSON.stringify(packet)
    const payload = new TextEncoder().encode(text)
    await this.room.localParticipant.publishData(payload, { reliable: true })
  }

  public onDataReceived(cb: (packet: DataPacket, participant?: LKParticipant) => void): () => void {
    this.onDataReceivedCallbacks.push(cb)
    return () => {
      this.onDataReceivedCallbacks = this.onDataReceivedCallbacks.filter((c) => c !== cb)
    }
  }

  public onParticipantUpdate(cb: () => void): () => void {
    this.onParticipantUpdateCallbacks.push(cb)
    return () => {
      this.onParticipantUpdateCallbacks = this.onParticipantUpdateCallbacks.filter((c) => c !== cb)
    }
  }

  public onActiveSpeakersChange(cb: (speakers: LKParticipant[]) => void): () => void {
    this.onActiveSpeakerChangeCallbacks.push(cb)
    return () => {
      this.onActiveSpeakerChangeCallbacks = this.onActiveSpeakerChangeCallbacks.filter((c) => c !== cb)
    }
  }

  public onConnectionStatusChange(cb: (status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void): () => void {
    this.onConnectionStatusChangeCallbacks.push(cb)
    return () => {
      this.onConnectionStatusChangeCallbacks = this.onConnectionStatusChangeCallbacks.filter((c) => c !== cb)
    }
  }

  public onScreenShareStopped(cb: () => void): () => void {
    this.onScreenShareStoppedCallbacks.push(cb)
    return () => {
      this.onScreenShareStoppedCallbacks = this.onScreenShareStoppedCallbacks.filter((c) => c !== cb)
    }
  }

  private notifyParticipantUpdate() {
    this.onParticipantUpdateCallbacks.forEach((cb) => cb())
  }

  public disconnect(): void {
    if (this.room) {
      try {
        this.room.disconnect()
      } catch (e) {
        console.warn('Error during disconnect:', e)
      }
      this.room = null
    }
  }
}

export const livekitManager = new LiveKitManager()
