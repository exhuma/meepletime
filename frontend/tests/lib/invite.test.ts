import { describe, it, expect } from 'vitest'
import {
  normalizePin,
  isValidPin,
  INVITE_ALPHABET,
  INVITE_LENGTH,
} from '../../src/lib/invite'

describe('normalizePin', () => {
  it('uppercases input', () => {
    expect(normalizePin('abc23m')).toBe('ABC23M')
  })

  it('strips characters outside the alphabet', () => {
    // O, I, L, 0, 1 are ambiguous and not in the alphabet.
    expect(normalizePin('A0O1I-L9')).toBe('A9')
  })

  it('strips separators and whitespace', () => {
    expect(normalizePin('ab 2-3 4m')).toBe('AB234M')
  })

  it('caps length at INVITE_LENGTH', () => {
    expect(normalizePin('ABCDEFGHJK').length).toBe(INVITE_LENGTH)
  })
})

describe('isValidPin', () => {
  it('accepts a full in-alphabet PIN', () => {
    expect(isValidPin('ABC234')).toBe(true)
  })

  it('rejects a too-short PIN', () => {
    expect(isValidPin('ABC2')).toBe(false)
  })

  it('rejects a PIN with out-of-alphabet characters', () => {
    expect(isValidPin('ABC2O4')).toBe(false)
  })
})

describe('alphabet constants', () => {
  it('excludes ambiguous characters', () => {
    for (const ch of '01OIL') {
      expect(INVITE_ALPHABET).not.toContain(ch)
    }
  })
})
