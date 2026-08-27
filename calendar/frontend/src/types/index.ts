export interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string | null
}

export interface CalendarInfo {
  id: string
  owner_id: string
  name: string
  color: string
  is_default: boolean
  created_at: string
}

export interface Attendee {
  id?: string
  event_id?: string
  user_id?: string | null
  email: string
  attendee_type?: 'internal' | 'external'
  rsvp_status?: 'pending' | 'yes' | 'no' | 'maybe'
  invitation_sent_at?: string | null
  reminder_sent_at?: string | null
}

export interface CalendarEvent {
  id: string
  calendar_id: string
  organizer_id: string
  title: string
  description?: string | null
  location?: string | null
  start_at: string
  end_at: string
  all_day: boolean
  recurrence_rule?: string | null
  reminder_minutes_before?: number
  meeting_id?: string | null
  meeting_link?: string | null
  source: 'calendar' | 'meet'
  color?: string | null
  created_at: string
  updated_at: string
  attendees: Attendee[]
  is_recurring_instance?: boolean
  parent_id?: string
}

export interface InAppNotificationItem {
  id: string
  user_id: string
  event_id?: string | null
  title: string
  message: string
  is_read: boolean
  created_at: string
}
