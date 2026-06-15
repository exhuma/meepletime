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
  isWeekend: boolean
}

/** English weekday short names indexed Sunday=0 … Saturday=6. */
const WEEKDAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const

/**
 * Read the locale's week info, tolerating the two browser shapes:
 * Chromium exposes `getWeekInfo()` (a method), Safari a `weekInfo`
 * property. Returns null when neither is available (e.g. Firefox).
 */
function localeWeekInfo(): { firstDay: number; weekend: number[] } | null {
  try {
    const loc = new Intl.Locale(navigator.language) as Intl.Locale & {
      getWeekInfo?: () => { firstDay: number; weekend: number[] }
      weekInfo?: { firstDay: number; weekend: number[] }
    }
    return loc.getWeekInfo?.() ?? loc.weekInfo ?? null
  } catch {
    return null
  }
}

/**
 * First weekday of the week for the user's locale, as a `getDay`
 * index (0 = Sunday … 6 = Saturday). Locale week info reports ISO
 * days (1 = Monday … 7 = Sunday), so `% 7` maps Sunday (7) to 0.
 * Falls back to Monday when the locale week info is unavailable.
 */
export function getWeekStart(): number {
  const info = localeWeekInfo()
  if (!info) return 1
  return info.firstDay % 7
}

/**
 * Weekend days for the user's locale as `getDay` indices. Falls back
 * to Saturday + Sunday when locale week info is unavailable.
 */
export function getWeekendDays(): Set<number> {
  const info = localeWeekInfo()
  if (!info) return new Set([0, 6])
  return new Set(info.weekend.map((d) => d % 7))
}

/** Weekday header labels ordered from `weekStart` (a `getDay` index). */
export function weekdayHeaders(weekStart: number): string[] {
  return Array.from({ length: 7 }, (_, i) => WEEKDAY_NAMES[(weekStart + i) % 7])
}

/** Format a Date as a `yyyy-MM-dd` key. */
export function formatDate(d: Date): string {
  return format(d, 'yyyy-MM-dd')
}

/** Human-readable "Month yyyy" label for the displayed month. */
export function monthLabel(monthStart: Date): string {
  return format(monthStart, 'MMMM yyyy')
}

/**
 * Number of leading blank cells before the month's first day, given
 * the locale's first weekday (`weekStart`, a `getDay` index). Defaults
 * to a Sunday-first week.
 */
export function firstDayOffset(monthStart: Date, weekStart = 0): number {
  return (getDay(monthStart) - weekStart + 7) % 7
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
  weekendDays: ReadonlySet<number> = new Set([0, 6]),
): MonthDayCell[] {
  const count = getDaysInMonth(monthStart)
  const cells: MonthDayCell[] = []
  for (let d = 1; d <= count; d++) {
    const day = new Date(monthStart.getFullYear(), monthStart.getMonth(), d)
    const date = formatDate(day)
    const entries = calendar[date] ?? []
    const mine = userId ? entries.find((a) => a.user_id === userId) : undefined
    cells.push({
      date,
      dayOfMonth: d,
      myState: mine?.state ?? null,
      viability: viability[date] ?? null,
      isWeekend: weekendDays.has(getDay(day)),
    })
  }
  return cells
}
