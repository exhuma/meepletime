import { describe, it, expect } from 'vitest'
import { nextAvailabilityState } from '../../src/lib/availability'

describe('nextAvailabilityState', () => {
  it('cycles empty -> attending', () => {
    expect(nextAvailabilityState(null)).toBe('attending')
  })

  it('cycles attending -> hosting', () => {
    expect(nextAvailabilityState('attending')).toBe('hosting')
  })

  it('cycles hosting -> empty', () => {
    expect(nextAvailabilityState('hosting')).toBe(null)
  })
})
