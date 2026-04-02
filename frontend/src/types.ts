export interface User {
  id: string
  email: string
  display_name: string | null
  created_at: string
}

export interface Circle {
  id: string
  name: string
  description: string | null
  image_ref: string | null
  timezone: string
  invite_token: string
  host_needed: boolean
  minimum_attendees: number | null
  soft_max_attendees: number | null
  hard_max_attendees: number | null
  external_links: unknown[] | null
  created_by_user_id: string
  created_at: string
  updated_at: string
}

export interface Member {
  id: string
  circle_id: string
  user_id: string
  pseudonym: string
  role: 'owner' | 'admin' | 'member'
  can_host_default: boolean
  joined_at: string
  notification_preferences: Record<string, unknown> | null
}

export interface Availability {
  id: string
  circle_id: string
  user_id: string
  local_date: string
  state: 'attending' | 'hosting'
  created_at: string
  updated_at: string
}

export interface DayViability {
  circle_id: string
  local_date: string
  attendee_count: number
  hosting_count: number
  is_viable: boolean
  is_soft_max_exceeded: boolean
  has_multiple_hosts_warning: boolean
  availabilities: Availability[]
}

export interface Note {
  id: string
  circle_id: string
  user_id: string
  local_date: string
  content: string
  created_at: string
  pseudonym?: string | null
}

export interface HostDayConstraint {
  id: string
  circle_id: string
  user_id: string
  local_date: string
  override_minimum_attendees: number | null
  override_soft_max_attendees: number | null
  override_hard_max_attendees: number | null
  created_at: string
  updated_at: string
}

export interface HostDayConstraintSet {
  override_minimum_attendees: number | null
  override_soft_max_attendees: number | null
  override_hard_max_attendees: number | null
}
