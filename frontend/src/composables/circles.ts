import { ref, readonly } from 'vue'
import type { DeepReadonly, Ref } from 'vue'
import api, { ApiError } from '../api'
import type {
  Availability,
  Circle,
  DayDescription,
  DayDescriptionBundle,
  DayViability,
  DeltaDoc,
  HostDayConstraint,
  HostDayConstraintSet,
  Member,
  Note,
} from '../types'

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

  /** Merge an updated circle into currentCircle and the list. */
  function syncCircle(updated: Circle): Circle {
    if (currentCircle.value?.id === updated.id) {
      currentCircle.value = updated
    }
    circles.value = circles.value.map((c) =>
      c.id === updated.id ? updated : c,
    )
    return updated
  }

  /** Update circle settings (owner/admin). Returns the updated circle. */
  async function updateCircle(
    id: string,
    data: Partial<Circle>,
  ): Promise<Circle> {
    return syncCircle(await api.patch<Circle>(`/circles/${id}`, data))
  }

  /** Upload/replace the circle hero image (owner/admin). */
  async function uploadCircleImage(id: string, file: File): Promise<Circle> {
    const form = new FormData()
    form.append('file', file)
    return syncCircle(await api.post<Circle>(`/circles/${id}/image`, form))
  }

  /** Remove the circle hero image (owner/admin). */
  async function deleteCircleImage(id: string): Promise<Circle> {
    return syncCircle(await api.delete<Circle>(`/circles/${id}/image`))
  }

  /** Fetch all members of circleId and update members state. */
  async function fetchMembers(circleId: string): Promise<void> {
    members.value = await api.get<Member[]>(`/circles/${circleId}/members`)
  }

  /** Fetch availability records for circleId in [startDate, endDate] and merge into calendar state. */
  async function fetchCalendar(
    circleId: string,
    startDate: string,
    endDate: string,
  ): Promise<void> {
    const items = await api.get<Availability[]>(
      `/circles/${circleId}/availability`,
      {
        params: { start_date: startDate, end_date: endDate },
      },
    )
    const dict: Record<string, Availability[]> = {}
    for (const item of items) {
      const key = String(item.local_date)
      if (!dict[key]) dict[key] = []
      dict[key].push(item)
    }
    calendar.value = dict
  }

  /** Set the current user's availability for date to state, updating calendar state. */
  async function setAvailability(
    circleId: string,
    date: string,
    state: 'attending' | 'hosting',
  ): Promise<void> {
    const updated = await api.put<Availability>(
      `/circles/${circleId}/availability/${date}`,
      { state },
    )
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
  async function deleteAvailability(
    circleId: string,
    date: string,
    userId: string,
  ): Promise<void> {
    await api.delete(`/circles/${circleId}/availability/${date}`)
    calendar.value = {
      ...calendar.value,
      [date]: (calendar.value[date] ?? []).filter((a) => a.user_id !== userId),
    }
  }

  /**
   * Cycle the current user's availability state for date.
   *
   * Implements: empty -> attending -> hosting -> empty.
   */
  async function cycleAvailability(
    circleId: string,
    date: string,
    userId: string,
  ): Promise<void> {
    const response = await api.post<{ availability: Availability | null }>(
      `/circles/${circleId}/availability/jobs`,
      {
        action: 'cycle',
        arguments: { local_date: date },
      },
    )
    if (response.availability) {
      const entries = [...(calendar.value[date] ?? [])]
      const idx = entries.findIndex((a) => a.user_id === userId)
      if (idx >= 0) {
        entries[idx] = response.availability
      } else {
        entries.push(response.availability)
      }
      calendar.value = { ...calendar.value, [date]: entries }
    } else {
      // Cycled to empty state
      calendar.value = {
        ...calendar.value,
        [date]: (calendar.value[date] ?? []).filter(
          (a) => a.user_id !== userId,
        ),
      }
    }
  }

  /** Fetch viability for circleId in [startDate, endDate] and merge into viability state. */
  async function fetchViability(
    circleId: string,
    startDate: string,
    endDate: string,
  ): Promise<void> {
    const items = await api.get<DayViability[]>(
      `/circles/${circleId}/viability`,
      {
        params: { start_date: startDate, end_date: endDate },
      },
    )
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
  async function addNote(
    circleId: string,
    date: string,
    content: string,
  ): Promise<Note> {
    return api.post<Note>(`/circles/${circleId}/notes/${date}`, { content })
  }

  /** Fetch the circle-wide and per-host descriptions for a day. */
  async function fetchDayDescriptions(
    circleId: string,
    date: string,
  ): Promise<DayDescriptionBundle> {
    return api.get<DayDescriptionBundle>(
      `/circles/${circleId}/day-description/${date}`,
    )
  }

  /** Create or replace the circle-wide description (owner/admin). */
  async function saveCircleDescription(
    circleId: string,
    date: string,
    contentDelta: DeltaDoc,
  ): Promise<DayDescription> {
    return api.put<DayDescription>(
      `/circles/${circleId}/day-description/${date}`,
      { content_delta: contentDelta },
    )
  }

  /** Delete the circle-wide description (owner/admin). */
  async function clearCircleDescription(
    circleId: string,
    date: string,
  ): Promise<void> {
    await api.delete(`/circles/${circleId}/day-description/${date}`)
  }

  /** Create or replace the caller's own host description for a day. */
  async function saveMyHostDescription(
    circleId: string,
    date: string,
    contentDelta: DeltaDoc,
  ): Promise<DayDescription> {
    return api.put<DayDescription>(
      `/circles/${circleId}/day-description/${date}/hosts/me`,
      { content_delta: contentDelta },
    )
  }

  /** Delete the caller's own host description for a day. */
  async function clearMyHostDescription(
    circleId: string,
    date: string,
  ): Promise<void> {
    await api.delete(`/circles/${circleId}/day-description/${date}/hosts/me`)
  }

  /** Join a circle using inviteToken with the given pseudonym. */
  async function joinCircle(
    inviteToken: string,
    pseudonym: string,
    canHostDefault: boolean,
  ): Promise<void> {
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

  /**
   * Fetch the current user's host constraint for circleId on date.
   * Returns null when no constraint has been set yet.
   */
  async function fetchMyConstraint(
    circleId: string,
    date: string,
  ): Promise<HostDayConstraint | null> {
    try {
      return await api.get<HostDayConstraint>(
        `/circles/${circleId}/host-constraints/me/${date}`,
      )
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return null
      throw err
    }
  }

  /**
   * Create or replace the current user's host constraint
   * for circleId on date.
   */
  async function setMyConstraint(
    circleId: string,
    date: string,
    data: HostDayConstraintSet,
  ): Promise<HostDayConstraint> {
    return api.put<HostDayConstraint>(
      `/circles/${circleId}/host-constraints/me/${date}`,
      data,
    )
  }

  /** Delete the current user's host constraint for circleId on date. */
  async function deleteMyConstraint(
    circleId: string,
    date: string,
  ): Promise<void> {
    await api.delete(`/circles/${circleId}/host-constraints/me/${date}`)
  }

  return {
    circles: readonly(circles) as DeepReadonly<Ref<Circle[]>>,
    currentCircle: readonly(currentCircle) as DeepReadonly<Ref<Circle | null>>,
    members: readonly(members) as DeepReadonly<Ref<Member[]>>,
    calendar: readonly(calendar) as DeepReadonly<
      Ref<Record<string, Availability[]>>
    >,
    viability: readonly(viability) as DeepReadonly<
      Ref<Record<string, DayViability>>
    >,
    fetchCircles,
    fetchCircle,
    createCircle,
    updateCircle,
    uploadCircleImage,
    deleteCircleImage,
    fetchMembers,
    fetchCalendar,
    setAvailability,
    deleteAvailability,
    cycleAvailability,
    fetchViability,
    fetchNotes,
    addNote,
    fetchDayDescriptions,
    saveCircleDescription,
    clearCircleDescription,
    saveMyHostDescription,
    clearMyHostDescription,
    joinCircle,
    regenerateInvite,
    fetchMyConstraint,
    setMyConstraint,
    deleteMyConstraint,
  }
}
