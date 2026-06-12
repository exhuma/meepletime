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
