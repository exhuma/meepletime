import { ref, readonly } from 'vue'
import type { DeepReadonly, Ref } from 'vue'
import api from '../api'
import type { Availability, Circle, DayViability, Member, Note } from '../types'

// Module-level singleton state
const circles = ref<Circle[]>([])
const currentCircle = ref<Circle | null>(null)
const members = ref<Member[]>([])
/** Availability keyed by date string YYYY-MM-DD. */
const calendar = ref<Record<string, Availability[]>>({})
/** Viability keyed by date string YYYY-MM-DD. */
const viability = ref<Record<string, DayViability>>({})

/** Return the reactive circle state and actions. */
export function useCircles() {
  /** Fetch all circles the current user belongs to and update state. */
  async function fetchCircles(): Promise<void> {
    circles.value = await api.get<Circle[]>('/circles')
  }

  /** Fetch a single circle by id and update currentCircle state. */
  async function fetchCircle(id: string): Promise<void> {
    currentCircle.value = await api.get<Circle>(`/circles/${id}`)
  }

  /** Create a new circle and append it to the circles list. Returns the created circle. */
  async function createCircle(data: Partial<Circle>): Promise<Circle> {
    const created = await api.post<Circle>('/circles', data)
    circles.value = [...circles.value, created]
    return created
  }

  /** Fetch all members of circleId and update members state. */
  async function fetchMembers(circleId: string): Promise<void> {
    members.value = await api.get<Member[]>(`/circles/${circleId}/members`)
  }

  /** Fetch availability records for circleId in [startDate, endDate] and merge into calendar state. */
  async function fetchCalendar(circleId: string, startDate: string, endDate: string): Promise<void> {
    const items = await api.get<Availability[]>(`/circles/${circleId}/availability`, {
      params: { start_date: startDate, end_date: endDate },
    })
    const dict: Record<string, Availability[]> = {}
    for (const item of items) {
      const key = String(item.local_date)
      if (!dict[key]) dict[key] = []
      dict[key].push(item)
    }
    calendar.value = { ...calendar.value, ...dict }
  }

  /** Set the current user's availability for date to state, updating calendar state. */
  async function setAvailability(circleId: string, date: string, state: 'attending' | 'hosting'): Promise<void> {
    const updated = await api.put<Availability>(`/circles/${circleId}/availability/${date}`, { state })
    const entries = [...(calendar.value[date] ?? [])]
    const idx = entries.findIndex((a) => a.user_id === updated.user_id)
    if (idx >= 0) {
      entries[idx] = updated
    } else {
      entries.push(updated)
    }
    calendar.value = { ...calendar.value, [date]: entries }
  }

  /** Delete the current user's availability for date. */
  async function deleteAvailability(circleId: string, date: string, userId: string): Promise<void> {
    await api.delete(`/circles/${circleId}/availability/${date}`)
    calendar.value = {
      ...calendar.value,
      [date]: (calendar.value[date] ?? []).filter((a) => a.user_id !== userId),
    }
  }

  /** Fetch viability for circleId in [startDate, endDate] and merge into viability state. */
  async function fetchViability(circleId: string, startDate: string, endDate: string): Promise<void> {
    const items = await api.get<DayViability[]>(`/circles/${circleId}/viability`, {
      params: { start_date: startDate, end_date: endDate },
    })
    const dict: Record<string, DayViability> = {}
    for (const item of items) {
      dict[String(item.local_date)] = item
    }
    viability.value = { ...viability.value, ...dict }
  }

  /** Fetch all notes for date in circleId. */
  async function fetchNotes(circleId: string, date: string): Promise<Note[]> {
    return api.get<Note[]>(`/circles/${circleId}/notes/${date}`)
  }

  /** Add a note with content for date in circleId. */
  async function addNote(circleId: string, date: string, content: string): Promise<Note> {
    return api.post<Note>(`/circles/${circleId}/notes/${date}`, { content })
  }

  /** Join a circle using inviteToken with the given pseudonym. */
  async function joinCircle(inviteToken: string, pseudonym: string, canHostDefault: boolean): Promise<void> {
    await api.post('/circles/join', {
      invite_token: inviteToken,
      pseudonym,
      can_host_default: canHostDefault,
    })
  }

  /** Regenerate the invite token for circleId. Returns updated circle. Requires owner/admin. */
  async function regenerateInvite(circleId: string): Promise<Circle> {
    const updated = await api.post<Circle>(`/circles/${circleId}/invite`)
    currentCircle.value = updated
    return updated
  }

  return {
    circles: readonly(circles) as DeepReadonly<Ref<Circle[]>>,
    currentCircle: readonly(currentCircle) as DeepReadonly<Ref<Circle | null>>,
    members: readonly(members) as DeepReadonly<Ref<Member[]>>,
    calendar: readonly(calendar) as DeepReadonly<Ref<Record<string, Availability[]>>>,
    viability: readonly(viability) as DeepReadonly<Ref<Record<string, DayViability>>>,
    fetchCircles,
    fetchCircle,
    createCircle,
    fetchMembers,
    fetchCalendar,
    setAvailability,
    deleteAvailability,
    fetchViability,
    fetchNotes,
    addNote,
    joinCircle,
    regenerateInvite,
  }
}
