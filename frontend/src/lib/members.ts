/**
 * Helpers that cross-reference availability entries with the member
 * roster: pseudonym resolution, role checks and the current user's
 * presence state.
 */
import type { Availability, Member } from '../types'

export interface EnrichedAttendee extends Availability {
  pseudonym: string
}

/** Attach each attendee's pseudonym, falling back to the user id. */
export function enrichAttendees(
  entries: readonly Availability[],
  members: readonly Member[],
): EnrichedAttendee[] {
  return entries.map((a) => {
    const member = members.find((m) => m.user_id === a.user_id)
    return { ...a, pseudonym: member?.pseudonym ?? a.user_id }
  })
}

/** The role of userId in the roster, or null when not a member. */
export function myRole(
  members: readonly Member[],
  userId: string | null,
): Member['role'] | null {
  if (!userId) return null
  return members.find((m) => m.user_id === userId)?.role ?? null
}

/** True when userId is an owner or admin of the circle. */
export function isAdminOrOwner(
  members: readonly Member[],
  userId: string | null,
): boolean {
  const role = myRole(members, userId)
  return role === 'owner' || role === 'admin'
}

/** The current user's presence state among entries, or null. */
export function myState(
  entries: readonly Availability[],
  userId: string | null,
): Availability['state'] | null {
  if (!userId) return null
  return entries.find((a) => a.user_id === userId)?.state ?? null
}
