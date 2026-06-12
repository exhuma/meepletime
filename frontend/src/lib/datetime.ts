/**
 * Date formatting that never throws: a malformed input is returned
 * verbatim instead of crashing the render.
 */
import { format, parseISO } from 'date-fns'

/** Format an ISO date/timestamp, returning the raw string on failure. */
export function safeFormat(iso: string, pattern: string): string {
  if (!iso) return ''
  try {
    return format(parseISO(iso), pattern)
  } catch {
    return iso
  }
}
