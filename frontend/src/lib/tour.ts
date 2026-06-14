/**
 * Thin wrapper around driver.js for the guided onboarding tour.
 *
 * Isolates the imperative library behind a single promise-returning
 * function so the rest of the app stays declarative. Resolves with the
 * keys of the tips whose popover was actually shown, so the caller can
 * persist exactly what the user saw (even if they close the tour early).
 */
import { driver, type DriveStep } from 'driver.js'
import 'driver.js/dist/driver.css'
import type { TourTip } from '../composables/tourRegistry'

/**
 * Run a guided tour for the given tips.
 *
 * Tips whose anchor element is not currently in the DOM are skipped, so
 * a mispositioned popover can never appear (e.g. a calendar cell that
 * has not rendered yet). Resolves with the keys of the tips that were
 * actually displayed.
 *
 * @param tips - Ordered tips to present.
 * @returns The keys of the tips whose popover was shown.
 */
export function runTour(tips: TourTip[]): Promise<string[]> {
  const present = tips.filter((t) => document.querySelector(t.selector))
  if (present.length === 0) return Promise.resolve([])

  return new Promise<string[]>((resolve) => {
    const shown = new Set<string>()
    const steps: DriveStep[] = present.map((tip) => ({
      element: tip.selector,
      popover: {
        title: tip.title,
        description: tip.body,
        // Marks the tip seen the moment its popover renders, so a
        // tip the user actually reached is not shown again next time.
        onPopoverRender: () => {
          shown.add(tip.key)
        },
      },
    }))

    const tour = driver({
      showProgress: true,
      progressText: '{{current}} of {{total}}',
      allowClose: true,
      steps,
      onDestroyed: () => resolve([...shown]),
    })
    tour.drive()
  })
}
