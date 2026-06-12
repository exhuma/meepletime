/**
 * Map a day's viability data to a semantic visual state.
 *
 * Components render colour/fill from the returned enum and flags rather
 * than encoding the rules inline, so the mapping lives in one tested
 * place.
 */
import type { DayViability } from '../types'

/** Background-fill intent for a calendar day. */
export type DayFill = 'viable' | 'over-soft-max' | 'neutral'

export interface DayVisualState {
  fill: DayFill
  isPast: boolean
  isDimmed: boolean
  multipleHostsWarning: boolean
  /** Attendee badge value, or null when there is nothing to show. */
  attendeeCount: number | null
}

/** Derive the visual state for a day from its viability and context. */
export function dayVisualState(
  viability: DayViability | null,
  opts: { isPast: boolean; dimmed: boolean },
): DayVisualState {
  let fill: DayFill = 'neutral'
  if (viability) {
    if (viability.is_soft_max_exceeded) fill = 'over-soft-max'
    else if (viability.is_viable) fill = 'viable'
  }
  const count = viability?.attendee_count ?? 0
  return {
    fill,
    isPast: opts.isPast,
    isDimmed: opts.dimmed,
    multipleHostsWarning: !!viability?.has_multiple_hosts_warning,
    attendeeCount: count > 0 ? count : null,
  }
}
