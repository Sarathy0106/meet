export interface User {
  id: string
  email: string
  display_name: string
  created_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  guestName: string | null
}

export interface Meeting {
  id: string
  code: string
  title: string
  host_id: string | null
  host_name: string | null
  scheduled_at: string | null
  lobby_enabled: boolean
  is_locked: boolean
  started_at: string | null
  ended_at: string | null
  created_at: string
  active_participants_count: number
}

export interface Participant {
  id: string
  meeting_id: string
  user_id: string | null
  guest_name: string | null
  display_name: string
  role: 'host' | 'co_host' | 'participant'
  status: 'waiting' | 'admitted' | 'rejected' | 'left'
  joined_at?: string
  left_at?: string | null
}

export interface ChatMessage {
  id: string
  meeting_id: string
  sender_name: string
  sender_id?: string | null
  content: string
  sent_at: string
  is_local?: boolean
}

export type DataPacketType = 
  | 'chat'
  | 'raise_hand'
  | 'lower_hand'
  | 'mute_participant'
  | 'kick_participant'
  | 'meeting_ended'

export interface DataPacket {
  type: DataPacketType
  senderId?: string
  senderName?: string
  targetId?: string
  payload?: any
  timestamp?: number
}
