import { describe, it, expect } from 'vitest'
import { dayVisualState } from '../../src/lib/viability'
import type { DayViability } from '../../src/types'

/** Build a DayViability with sane defaults overridable per test. */
function via(p: Partial<DayViability>): DayViability {
  return {
    circle_id: 'c',
    local_date: '2026-06-12',
    attendee_count: 0,
    hosting_count: 0,
    is_viable: false,
    is_soft_max_exceeded: false,
    has_multiple_hosts_warning: false,
    availabilities: [],
    ...p,
  }
}

const plain = { isPast: false, dimmed: false }

describe('dayVisualState', () => {
  it('is neutral when there is no viability data', () => {
    const s = dayVisualState(null, plain)
    expect(s.fill).toBe('neutral')
    expect(s.attendeeCount).toBe(null)
  })

  it('is viable when viable and not over soft max', () => {
    expect(dayVisualState(via({ is_viable: true }), plain).fill).toBe('viable')
  })

  it('over-soft-max takes precedence over viable', () => {
    const s = dayVisualState(
      via({ is_viable: true, is_soft_max_exceeded: true }),
      plain,
    )
    expect(s.fill).toBe('over-soft-max')
  })

  it('exposes attendee count only when positive', () => {
    expect(
      dayVisualState(via({ attendee_count: 3 }), plain).attendeeCount,
    ).toBe(3)
    expect(
      dayVisualState(via({ attendee_count: 0 }), plain).attendeeCount,
    ).toBe(null)
  })

  it('passes through past, dimmed and warning flags', () => {
    const s = dayVisualState(via({ has_multiple_hosts_warning: true }), {
      isPast: true,
      dimmed: true,
    })
    expect(s.isPast).toBe(true)
    expect(s.isDimmed).toBe(true)
    expect(s.multipleHostsWarning).toBe(true)
  })
})
