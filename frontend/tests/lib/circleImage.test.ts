// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import {
  resolveImageUrl,
  validateImageFile,
  MAX_IMAGE_BYTES,
} from '../../src/lib/circleImage'

describe('resolveImageUrl', () => {
  it('returns null for empty refs', () => {
    expect(resolveImageUrl(null)).toBeNull()
    expect(resolveImageUrl(undefined)).toBeNull()
    expect(resolveImageUrl('')).toBeNull()
  })

  it('passes through absolute and data URLs unchanged', () => {
    expect(resolveImageUrl('https://cdn.example/x.png')).toBe(
      'https://cdn.example/x.png',
    )
    expect(resolveImageUrl('data:image/png;base64,AAAA')).toBe(
      'data:image/png;base64,AAAA',
    )
  })

  it('resolves a relative API path against the API base', () => {
    const url = resolveImageUrl('/circles/abc/image?v=42')
    expect(url).toBe('http://localhost:8000/circles/abc/image?v=42')
  })
})

describe('validateImageFile', () => {
  it('accepts a small PNG', () => {
    const file = new File([new Uint8Array(10)], 'a.png', {
      type: 'image/png',
    })
    expect(validateImageFile(file)).toBeNull()
  })

  it('rejects an unsupported type', () => {
    const file = new File([new Uint8Array(10)], 'a.txt', {
      type: 'text/plain',
    })
    expect(validateImageFile(file)).toMatch(/JPEG, PNG, or WebP/)
  })

  it('rejects an oversized file', () => {
    const file = new File([new Uint8Array(MAX_IMAGE_BYTES + 1)], 'big.png', {
      type: 'image/png',
    })
    expect(validateImageFile(file)).toMatch(/too large/)
  })
})
