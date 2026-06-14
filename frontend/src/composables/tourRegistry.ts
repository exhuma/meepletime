/**
 * Static registry of guided-tour tips.
 *
 * Each tip is anchored to a DOM element (via a `data-tour` attribute)
 * and belongs to a single view. The onboarding composable selects, at
 * most, a small number of unseen tips per view-visit so that returning
 * users are introduced to features gradually rather than all at once.
 *
 * Tip `key`s are persisted server-side in the user's `seen_tips` set,
 * so they must be stable: never rename or reuse a key.
 */

/** Views that can trigger a tour. */
export type ViewKey = 'circles' | 'calendar' | 'circleList' | 'dayDetail'

/** A single guided-tour tip anchored to a DOM element. */
export interface TourTip {
  /** Stable key persisted in `seen_tips`; never reused or renamed. */
  key: string
  /** The view this tip belongs to (matches `startTour` argument). */
  view: ViewKey
  /** CSS selector for the anchor element (a `data-tour` attribute). */
  selector: string
  /** Short popover heading. */
  title: string
  /** Popover body copy. */
  body: string
  /** Lower runs first within a view; essentials get the lowest. */
  priority: number
  /** Shown on the first visit to a view; others trickle in later. */
  essential: boolean
}

/**
 * The full set of tour tips, grouped by view. Copy is seeded from the
 * user guide (`docs/user/index.md`). Keep the count of `essential`
 * tips per view at or below the per-visit cap so first visits stay
 * light.
 */
export const TOUR_TIPS: TourTip[] = [
  // --- Circles landing ---
  {
    key: 'circles.create',
    view: 'circles',
    selector: '[data-tour="circles-create"]',
    title: 'Create a circle',
    body:
      'A circle is a private group of friends sharing a calendar. ' +
      'Create one here and invite the others.',
    priority: 10,
    essential: true,
  },
  {
    key: 'circles.join',
    view: 'circles',
    selector: '[data-tour="circles-join"]',
    title: 'Joining a circle',
    body:
      'Got an invite link or PIN? Join an existing circle here — ' +
      'you only ever see circles you have been invited to.',
    priority: 20,
    essential: false,
  },
  // --- Circle calendar ---
  {
    key: 'calendar.tapCycle',
    view: 'calendar',
    selector: '[data-tour="calendar-grid"]',
    title: 'Tap to set availability',
    body:
      'Tap a day to cycle your own state: ' +
      'empty → attending → hosting → empty. Changes save instantly.',
    priority: 10,
    essential: true,
  },
  {
    key: 'calendar.tabs',
    view: 'calendar',
    selector: '[data-tour="circle-tabs"]',
    title: 'Calendar and List',
    body:
      'Switch between the month grid for tapping availability and a ' +
      'List of upcoming days — the quickest way to see when you can meet.',
    priority: 20,
    essential: true,
  },
  {
    key: 'calendar.legend',
    view: 'calendar',
    selector: '[data-tour="calendar-legend"]',
    title: 'Reading the markers',
    body:
      'A day becomes a possible meetup once someone is attending or ' +
      'hosting. These chips explain the viability markers.',
    priority: 30,
    essential: false,
  },
  // --- Day detail ---
  {
    key: 'dayDetail.intro',
    view: 'dayDetail',
    selector: '[data-tour="day-detail-header"]',
    title: 'Day details',
    body:
      'See who can attend or host on this day, and read or add a ' +
      'note for everyone in the circle.',
    priority: 10,
    essential: true,
  },
]
