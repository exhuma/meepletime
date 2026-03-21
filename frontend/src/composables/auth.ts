import { ref, readonly, computed } from 'vue'
import type { ComputedRef, DeepReadonly, Ref } from 'vue'
import api from '../api'
import type { User } from '../types'

// Module-level singleton state shared across all component instances
const token = ref<string | null>(localStorage.getItem('meepletime_token'))
const user = ref<User | null>(null)

/** Return the reactive auth state and actions for the signed-in user. */
export function useAuth() {
  /** True when a valid JWT token is present in state. */
  const isLoggedIn: ComputedRef<boolean> = computed(() => token.value !== null)

  /**
   * Authenticate with email/password, store the JWT, and fetch the user profile.
   */
  async function login(email: string, password: string): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const data = await api.post<{ access_token: string }>('/auth/token', formData)
    token.value = data.access_token
    localStorage.setItem('meepletime_token', token.value)
    await fetchMe()
  }

  /** Register a new account. Does not log in automatically. */
  async function register(email: string, password: string): Promise<void> {
    await api.post('/auth/register', { email, password })
  }

  /** Clear the session token and user from state and localStorage. */
  function logout(): void {
    token.value = null
    user.value = null
    localStorage.removeItem('meepletime_token')
  }

  /** Restore auth state from localStorage on app startup. */
  async function loadFromStorage(): Promise<void> {
    const stored = localStorage.getItem('meepletime_token')
    if (stored) {
      token.value = stored
      try {
        await fetchMe()
      } catch {
        // expired token — unauthorized handler redirects
      }
    }
  }

  /** Fetch the authenticated user's profile from /auth/me and update state. */
  async function fetchMe(): Promise<void> {
    user.value = await api.get<User>('/auth/me')
  }

  return {
    user: readonly(user) as DeepReadonly<Ref<User | null>>,
    token: readonly(token),
    isLoggedIn,
    login,
    register,
    logout,
    loadFromStorage,
  }
}
