import { describe, it, expect } from 'vitest'
import {
  formatDate,
  monthLabel,
  firstDayOffset,
  weekdayHeaders,
  canGoToPrevMonth,
  buildMonthDays,
  buildUpcomingDays,
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
  it('counts blank cells for a Sunday-first week (default)', () => {
    // 2026-06-01 is a Monday -> one blank cell before it (Sunday).
    expect(firstDayOffset(new Date(2026, 5, 1))).toBe(1)
  })

  it('counts blank cells for a Monday-first week', () => {
    // 2026-06-01 is a Monday -> no blank cells when Monday leads.
    expect(firstDayOffset(new Date(2026, 5, 1), 1)).toBe(0)
  })
})

describe('weekdayHeaders', () => {
  it('orders headers from Sunday for a Sunday-first week', () => {
    expect(weekdayHeaders(0)).toEqual([
      'Sun',
      'Mon',
      'Tue',
      'Wed',
      'Thu',
      'Fri',
      'Sat',
    ])
  })

  it('orders headers from Monday for a Monday-first week', () => {
    expect(weekdayHeaders(1)).toEqual([
      'Mon',
      'Tue',
      'Wed',
      'Thu',
      'Fri',
      'Sat',
      'Sun',
    ])
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

  it('flags weekend days from the given weekend set', () => {
    const days = buildMonthDays(
      new Date(2026, 5, 1),
      {},
      {},
      null,
      new Set([0, 6]),
    )
    // 2026-06-01 Monday, 06-06 Saturday, 06-07 Sunday.
    expect(days[0].isWeekend).toBe(false)
    expect(days[5].isWeekend).toBe(true)
    expect(days[6].isWeekend).toBe(true)
  })
})

describe('buildUpcomingDays', () => {
  const day = (over: Partial<DayViability>): DayViability =>
    ({
      attendee_count: 0,
      is_viable: false,
      ...over,
    }) as DayViability

  const viability: Record<string, DayViability> = {
    '2026-06-10': day({ attendee_count: 0, is_viable: false }),
    '2026-06-12': day({ attendee_count: 2, is_viable: true }),
    '2026-06-11': day({ attendee_count: 1, is_viable: false }),
    '2026-06-15': day({ attendee_count: 3, is_viable: true }),
  }

  it('drops days before fromDate and days with no attendees', () => {
    const rows = buildUpcomingDays(viability, '2026-06-12', false)
    // 2026-06-10 (before) and 2026-06-11 (before) excluded; both
    // remaining have attendees.
    expect(rows.map((r) => r.date)).toEqual(['2026-06-12', '2026-06-15'])
  })

  it('keeps zero-attendee days out even when in range', () => {
    const rows = buildUpcomingDays(viability, '2026-06-10', false)
    // 2026-06-10 has zero attendees -> excluded.
    expect(rows.map((r) => r.date)).toEqual([
      '2026-06-11',
      '2026-06-12',
      '2026-06-15',
    ])
  })

  it('drops non-viable days when viableOnly is true', () => {
    const rows = buildUpcomingDays(viability, '2026-06-10', true)
    expect(rows.map((r) => r.date)).toEqual(['2026-06-12', '2026-06-15'])
  })

  it('returns days in chronological order', () => {
    const rows = buildUpcomingDays(viability, '2026-06-01', false)
    const dates = rows.map((r) => r.date)
    expect(dates).toEqual([...dates].sort())
  })
})
