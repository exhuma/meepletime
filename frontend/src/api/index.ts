/**
 * Vanilla fetch API client.
 *
 * Token acquisition is delegated to the TokenProvider in ./token,
 * keeping the transport layer decoupled from how credentials are
 * obtained (local auth today, oidc-client-ts tomorrow).
 */
import { getToken } from './token'

export { setTokenProvider } from './token'
export type { TokenProvider } from './token'

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)
  ?? 'http://localhost:8000'

let _onUnauthorized: (() => void) | null = null

/**
 * Register a callback invoked when the API returns HTTP 401.
 *
 * Today:      () => router.push('/login')
 * With OIDC:  () => userManager.signinRedirect()
 */
export function setUnauthorizedHandler(handler: () => void): void {
  _onUnauthorized = handler
}

/** Thrown for any non-2xx API response. */
export class ApiError extends Error {
  readonly status: number
  /** Parsed JSON body from the error response, if available. */
  readonly data: unknown

  constructor(status: number, data: unknown) {
    super(`API error ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function request<T>(
  method: string,
  path: string,
  {
    body,
    params,
  }: { body?: unknown; params?: Record<string, string> } = {},
): Promise<T> {
  const url = new URL(path, BASE)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      url.searchParams.set(k, v)
    }
  }

  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let fetchBody: BodyInit | undefined
  if (body != null) {
    if (body instanceof URLSearchParams) {
      fetchBody = body
      // Browser sets Content-Type automatically for URLSearchParams
    } else {
      headers['Content-Type'] = 'application/json'
      fetchBody = JSON.stringify(body)
    }
  }

  const res = await fetch(url.toString(), { method, headers, body: fetchBody })

  if (res.status === 401) {
    _onUnauthorized?.()
  }

  if (!res.ok) {
    let data: unknown = null
    try { data = await res.json() } catch { /* non-JSON error body */ }
    throw new ApiError(res.status, data)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const api = {
  get<T>(
    path: string,
    options?: { params?: Record<string, string> },
  ): Promise<T> {
    return request<T>('GET', path, options)
  },

  post<T = void>(path: string, body?: unknown): Promise<T> {
    return request<T>('POST', path, { body })
  },

  put<T = void>(path: string, body?: unknown): Promise<T> {
    return request<T>('PUT', path, { body })
  },

  delete(path: string): Promise<void> {
    return request<void>('DELETE', path)
  },
}

export default api
