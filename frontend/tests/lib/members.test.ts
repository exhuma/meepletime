import { describe, it, expect } from 'vitest'
import {
  enrichAttendees,
  myRole,
  isAdminOrOwner,
  myState,
} from '../../src/lib/members'
import type { Availability, Member } from '../../src/types'

const members = [
  { user_id: 'u1', role: 'owner', pseudonym: 'Ann' },
  { user_id: 'u2', role: 'admin', pseudonym: 'Bob' },
  { user_id: 'u3', role: 'member', pseudonym: 'Cat' },
] as unknown as Member[]

const entries = [
  { user_id: 'u1', state: 'attending' },
  { user_id: 'u9', state: 'hosting' },
] as unknown as Availability[]

describe('enrichAttendees', () => {
  it('resolves pseudonyms from the members list', () => {
    const result = enrichAttendees(entries, members)
    expect(result[0].pseudonym).toBe('Ann')
  })

  it('falls back to the user id for unknown members', () => {
    const result = enrichAttendees(entries, members)
    expect(result[1].pseudonym).toBe('u9')
  })
})

describe('myRole', () => {
  it('returns the role of the matching member', () => {
    expect(myRole(members, 'u2')).toBe('admin')
  })

  it('returns null when the user is not a member', () => {
    expect(myRole(members, 'nobody')).toBe(null)
  })
})

describe('isAdminOrOwner', () => {
  it('is true for owners and admins', () => {
    expect(isAdminOrOwner(members, 'u1')).toBe(true)
    expect(isAdminOrOwner(members, 'u2')).toBe(true)
  })

  it('is false for plain members and non-members', () => {
    expect(isAdminOrOwner(members, 'u3')).toBe(false)
    expect(isAdminOrOwner(members, 'nobody')).toBe(false)
  })
})

describe('myState', () => {
  it('returns the current user presence state', () => {
    expect(myState(entries, 'u1')).toBe('attending')
  })

  it('returns null when the user has no entry', () => {
    expect(myState(entries, 'u3')).toBe(null)
  })
})
