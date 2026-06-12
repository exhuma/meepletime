/**
 * Availability state-cycle logic.
 *
 * A day's presence for the current user cycles through three states
 * on each tap: empty -> attending -> hosting -> empty. The backend is
 * authoritative, but this pure helper lets the client and its tests
 * share one definition of the order.
 */

/** A concrete presence state (the absence of one is modelled as null). */
export type PresenceState = 'attending' | 'hosting'

/** Return the next presence state in the cycle. */
export function nextAvailabilityState(
  state: PresenceState | null,
): PresenceState | null {
  if (state === null) return 'attending'
  if (state === 'attending') return 'hosting'
  return null
}
