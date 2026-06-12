import { describe, it, expect } from 'vitest'
import { safeFormat } from '../../src/lib/datetime'

describe('safeFormat', () => {
  it('formats an ISO date with the given pattern', () => {
    expect(safeFormat('2026-06-12', 'yyyy/MM/dd')).toBe('2026/06/12')
  })

  it('formats an ISO timestamp', () => {
    expect(safeFormat('2026-06-12T08:30:00', 'MMM d, HH:mm')).toBe(
      'Jun 12, 08:30',
    )
  })

  it('returns an empty string for empty input', () => {
    expect(safeFormat('', 'yyyy')).toBe('')
  })

  it('returns the raw input when it cannot be parsed', () => {
    expect(safeFormat('not-a-date', 'yyyy')).toBe('not-a-date')
  })
})
