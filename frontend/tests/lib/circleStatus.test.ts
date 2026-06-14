import { describe, it, expect } from 'vitest'
import { nextViableDate } from '../../src/lib/circleStatus'
import type { DayViability } from '../../src/types'

// DayViability uses `local_date` (not `date`) — adapter keeps test readable.
const v = (local_date: string, is_viable: boolean): DayViability =>
  ({
    circle_id: 'c',
    local_date,
    attendee_count: 0,
    hosting_count: 0,
    is_viable,
    is_soft_max_exceeded: false,
    has_multiple_hosts_warning: false,
    availabilities: [],
  }) as DayViability

describe('nextViableDate', () => {
  it('returns the earliest viable date on or after today', () => {
    const map = {
      '2026-06-10': v('2026-06-10', true),
      '2026-06-20': v('2026-06-20', true),
      '2026-06-25': v('2026-06-25', false),
    }
    expect(nextViableDate(map, '2026-06-14')).toBe('2026-06-20')
  })

  it('returns null when no upcoming day is viable', () => {
    const map = { '2026-06-10': v('2026-06-10', true) }
    expect(nextViableDate(map, '2026-06-14')).toBeNull()
  })
})
