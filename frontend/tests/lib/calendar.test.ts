import { describe, it, expect } from 'vitest'
import {
  formatDate,
  monthLabel,
  firstDayOffset,
  canGoToPrevMonth,
  buildMonthDays,
} from '../../src/lib/calendar'
import type { Availability, DayViability } from '../../src/types'

describe('formatDate', () => {
  it('formats a Date as yyyy-MM-dd', () => {
    expect(formatDate(new Date(2026, 5, 9))).toBe('2026-06-09')
  })
})

describe('monthLabel', () => {
  it('formats the month and year', () => {
    expect(monthLabel(new Date(2026, 5, 1))).toBe('June 2026')
  })
})

describe('firstDayOffset', () => {
  it('returns the weekday index of the month start', () => {
    // 2026-06-01 is a Monday -> 1.
    expect(firstDayOffset(new Date(2026, 5, 1))).toBe(1)
  })
})

describe('canGoToPrevMonth', () => {
  it('is false when already at the current month', () => {
    expect(canGoToPrevMonth(new Date(2026, 5, 1), new Date(2026, 5, 12))).toBe(
      false,
    )
  })

  it('is true when the displayed month is after the current one', () => {
    expect(canGoToPrevMonth(new Date(2026, 6, 1), new Date(2026, 5, 12))).toBe(
      true,
    )
  })
})

describe('buildMonthDays', () => {
  it('builds one cell per day with my state and viability', () => {
    const calendar: Record<string, Availability[]> = {
      '2026-06-02': [
        { user_id: 'u1', state: 'hosting' } as unknown as Availability,
      ],
    }
    const viability: Record<string, DayViability> = {
      '2026-06-02': { is_viable: true } as unknown as DayViability,
    }
    const days = buildMonthDays(new Date(2026, 5, 1), calendar, viability, 'u1')
    expect(days).toHaveLength(30)
    expect(days[0].date).toBe('2026-06-01')
    expect(days[0].myState).toBe(null)
    expect(days[1].myState).toBe('hosting')
    expect(days[1].viability?.is_viable).toBe(true)
  })

  it('ignores availability belonging to other users', () => {
    const calendar: Record<string, Availability[]> = {
      '2026-06-01': [
        { user_id: 'u2', state: 'attending' } as unknown as Availability,
      ],
    }
    const days = buildMonthDays(new Date(2026, 5, 1), calendar, {}, 'u1')
    expect(days[0].myState).toBe(null)
  })
})
