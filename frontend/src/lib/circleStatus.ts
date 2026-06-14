import type { DayViability } from '../types'

/**
 * Earliest viable date on or after `todayStr` (ISO yyyy-MM-dd), or null.
 * Pure: operates on the viability map already loaded by the circles
 * composable. No network.
 */
export function nextViableDate(
  viability: Record<string, DayViability>,
  todayStr: string,
): string | null {
  const upcoming = Object.values(viability)
    .filter((d) => d.is_viable && d.local_date >= todayStr)
    .map((d) => d.local_date)
    .sort()
  return upcoming[0] ?? null
}
