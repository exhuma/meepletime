// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { rememberCircle, lastCircleId } from '../../src/composables/lastCircle'

beforeEach(() => localStorage.clear())

describe('lastCircle', () => {
  it('remembers and reads back the last circle id', () => {
    expect(lastCircleId()).toBeNull()
    rememberCircle('abc')
    expect(lastCircleId()).toBe('abc')
  })

  it('overwrites the previous id when called again', () => {
    rememberCircle('abc')
    rememberCircle('xyz')
    expect(lastCircleId()).toBe('xyz')
  })
})
