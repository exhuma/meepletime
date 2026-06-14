const KEY = 'mt:last-circle'

/** Persist the most recently opened circle id. */
export function rememberCircle(id: string): void {
  try {
    localStorage.setItem(KEY, id)
  } catch {
    /* storage unavailable — nav just falls back to the list */
  }
}

/** The last opened circle id, or null. */
export function lastCircleId(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}
