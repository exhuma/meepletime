// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../src/api', () => {
  class ApiError extends Error {}
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
    ApiError,
  }
})

import api from '../../src/api'
import { useCircles } from '../../src/composables/circles'
import type { Circle } from '../../src/types'

const mockApi = api as unknown as {
  post: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

function makeCircle(overrides: Partial<Circle> = {}): Circle {
  return {
    id: 'c1',
    name: 'Test',
    description: null,
    image_ref: null,
    timezone: 'UTC',
    invite_token: 'ABCDEF',
    host_needed: false,
    minimum_attendees: null,
    soft_max_attendees: null,
    hard_max_attendees: null,
    external_links: null,
    created_by_user_id: 'u1',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useCircles image + update actions', () => {
  it('updateCircle PATCHes the circle and returns it', async () => {
    const updated = makeCircle({ name: 'Renamed' })
    mockApi.patch.mockResolvedValue(updated)

    const { updateCircle } = useCircles()
    const result = await updateCircle('c1', { name: 'Renamed' })

    expect(mockApi.patch).toHaveBeenCalledWith('/circles/c1', {
      name: 'Renamed',
    })
    expect(result).toEqual(updated)
  })

  it('uploadCircleImage POSTs FormData carrying the file', async () => {
    const withImage = makeCircle({ image_ref: '/circles/c1/image?v=1' })
    mockApi.post.mockResolvedValue(withImage)
    const file = new File([new Uint8Array(4)], 'hero.png', {
      type: 'image/png',
    })

    const { uploadCircleImage } = useCircles()
    const result = await uploadCircleImage('c1', file)

    expect(mockApi.post).toHaveBeenCalledTimes(1)
    const [path, body] = mockApi.post.mock.calls[0]
    expect(path).toBe('/circles/c1/image')
    expect(body).toBeInstanceOf(FormData)
    expect((body as FormData).get('file')).toBe(file)
    expect(result).toEqual(withImage)
  })

  it('deleteCircleImage DELETEs the image endpoint', async () => {
    const cleared = makeCircle({ image_ref: null })
    mockApi.delete.mockResolvedValue(cleared)

    const { deleteCircleImage } = useCircles()
    const result = await deleteCircleImage('c1')

    expect(mockApi.delete).toHaveBeenCalledWith('/circles/c1/image')
    expect(result).toEqual(cleared)
  })
})
