/**
 * Pure month-grid construction for the circle calendar: day-cell
 * assembly plus the small date helpers the view needs (label, weekday
 * offset, past-month guard).
 */
import {
  format,
  addMonths,
  startOfMonth,
  getDaysInMonth,
  getDay,
} from 'date-fns'
import type { Availability, DayViability } from '../types'

/** One rendered day of the calendar grid. */
export interface MonthDayCell {
  date: string
  dayOfMonth: number
  myState: Availability['state'] | null
  viability: DayViability | null
}

/** Format a Date as a `yyyy-MM-dd` key. */
export function formatDate(d: Date): string {
  return format(d, 'yyyy-MM-dd')
}

/** Human-readable "Month yyyy" label for the displayed month. */
export function monthLabel(monthStart: Date): string {
  return format(monthStart, 'MMMM yyyy')
}

/** Weekday index (0 = Sunday) of the month's first day. */
export function firstDayOffset(monthStart: Date): number {
  return getDay(monthStart)
}

/** True when navigating back stays at or after the current month. */
export function canGoToPrevMonth(monthStart: Date, today: Date): boolean {
  return addMonths(monthStart, -1) >= startOfMonth(today)
}

/** One upcoming meetup-candidate day for the list view. */
export interface UpcomingDay {
  date: string
  viability: DayViability
}

/**
 * Select upcoming meetup-candidate days for the list view.
 *
 * Includes only days on or after `fromDate` that have at least one
 * attendee. When `viableOnly` is true, non-viable days are dropped too.
 * Days are returned in chronological order. `fromDate` and the
 * viability keys are `yyyy-MM-dd`, so lexical comparison is also
 * chronological.
 *
 * @param viability - Viability keyed by `yyyy-MM-dd`.
 * @param fromDate - Earliest day to include (inclusive), `yyyy-MM-dd`.
 * @param viableOnly - When true, drop days that are not viable.
 * @returns Chronologically sorted upcoming days.
 */
export function buildUpcomingDays(
  viability: Readonly<Record<string, DayViability>>,
  fromDate: string,
  viableOnly: boolean,
): UpcomingDay[] {
  const rows: UpcomingDay[] = []
  for (const [date, day] of Object.entries(viability)) {
    if (date < fromDate) continue
    if (day.attendee_count < 1) continue
    if (viableOnly && !day.is_viable) continue
    rows.push({ date, viability: day })
  }
  rows.sort((a, b) => a.date.localeCompare(b.date))
  return rows
}

/** Build the day cells for monthStart, merging in the user's state. */
export function buildMonthDays(
  monthStart: Date,
  calendar: Readonly<Record<string, readonly Availability[]>>,
  viability: Readonly<Record<string, DayViability>>,
  userId: string | null,
): MonthDayCell[] {
  const count = getDaysInMonth(monthStart)
  const cells: MonthDayCell[] = []
  for (let d = 1; d <= count; d++) {
    const date = formatDate(
      new Date(monthStart.getFullYear(), monthStart.getMonth(), d),
    )
    const entries = calendar[date] ?? []
    const mine = userId ? entries.find((a) => a.user_id === userId) : undefined
    cells.push({
      date,
      dayOfMonth: d,
      myState: mine?.state ?? null,
      viability: viability[date] ?? null,
    })
  }
  return cells
}
