/**
 * Re-authentication loop breaker.
 *
 * A 401 from the API means the stored access token was rejected by the
 * resource server — it is expired, or Keycloak's signing keys rotated
 * after a restart so the (still clock-valid) token no longer verifies.
 * The correct response is to discard the token and sign in again, which
 * self-heals via the Keycloak SSO session.
 *
 * To avoid an infinite redirect loop when even a *freshly issued* token
 * is rejected (a genuine backend misconfiguration, not a stale token),
 * we remember when we last re-authenticated. If another 401 arrives
 * within {@link LOOP_WINDOW_MS}, we stop redirecting and surface a
 * manual sign-in instead. State lives in sessionStorage so it survives
 * the full-page redirect to Keycloak and back.
 */
const REAUTH_AT_KEY = 'mt.reauthAt'
const AUTH_ERROR_KEY = 'mt.authError'
const LOOP_WINDOW_MS = 15_000

/** True if we re-authenticated within the loop window (fresh token also failing). */
export function recentlyReauthed(now: number = Date.now()): boolean {
  const last = Number(sessionStorage.getItem(REAUTH_AT_KEY) ?? '0')
  return last > 0 && now - last < LOOP_WINDOW_MS
}

/** Record that a re-authentication redirect is being initiated now. */
export function markReauthAttempt(now: number = Date.now()): void {
  sessionStorage.setItem(REAUTH_AT_KEY, String(now))
}

/** Clear the guard after a successful authenticated API call. */
export function clearReauthGuard(): void {
  sessionStorage.removeItem(REAUTH_AT_KEY)
  sessionStorage.removeItem(AUTH_ERROR_KEY)
}

/** Enter the terminal error state: stop auto-redirecting, ask the user. */
export function setAuthError(): void {
  sessionStorage.setItem(AUTH_ERROR_KEY, '1')
  sessionStorage.removeItem(REAUTH_AT_KEY)
}

/** True when auto sign-in has been suppressed after repeated failure. */
export function hasAuthError(): boolean {
  return sessionStorage.getItem(AUTH_ERROR_KEY) === '1'
}
