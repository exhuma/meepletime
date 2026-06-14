/**
 * Onboarding composable: backend-persisted welcome + guided-tour state.
 *
 * State is loaded once from `GET /onboarding` on startup and kept as a
 * module-level singleton (mirroring `useNotificationSettings`). Each
 * view calls `startTour(view)` from its `onMounted`; this picks up to
 * `MAX_TIPS_PER_VISIT` unseen tips for that view, runs them, and
 * persists the keys actually shown so they are not repeated.
 */
import { ref, computed, readonly } from 'vue'
import type { ComputedRef } from 'vue'
import api from '../api'
import type { OnboardingState } from '../types'
import { TOUR_TIPS, type TourTip, type ViewKey } from './tourRegistry'
import { runTour } from '../lib/tour'

/** Cap on how many tips a single view-visit may introduce. */
const MAX_TIPS_PER_VISIT = 3

// Module-level singleton state for the current user's onboarding.
const state = ref<OnboardingState | null>(null)
const loaded = ref(false)

/** Return reactive onboarding state and actions. */
export function useOnboarding() {
  /** Fetch the current user's onboarding state (creates defaults). */
  async function load(): Promise<void> {
    state.value = await api.get<OnboardingState>('/onboarding')
    loaded.value = true
  }

  /** True once the welcome intro has been seen. */
  const welcomeSeen: ComputedRef<boolean> = computed(
    () => state.value?.welcome_seen ?? false,
  )

  /** Mark the welcome intro as seen and store the updated state. */
  async function markWelcomeSeen(): Promise<void> {
    state.value = await api.put<OnboardingState>('/onboarding/welcome', {
      welcome_seen: true,
    })
  }

  /**
   * Pick up to `MAX_TIPS_PER_VISIT` unseen tips for a view, ordered
   * essential-first then by ascending priority.
   */
  function selectTips(view: ViewKey): TourTip[] {
    const seen = new Set(state.value?.seen_tips ?? [])
    return TOUR_TIPS.filter((t) => t.view === view && !seen.has(t.key))
      .sort((a, b) => {
        if (a.essential !== b.essential) return a.essential ? -1 : 1
        return a.priority - b.priority
      })
      .slice(0, MAX_TIPS_PER_VISIT)
  }

  /**
   * Start the tour for a view, if state is loaded, the welcome flow is
   * done, and there are unseen tips. Persists the keys actually shown.
   *
   * The cap is per view-visit, so each view runs its own fresh
   * "1 of N" sequence.
   */
  async function startTour(view: ViewKey): Promise<void> {
    if (!loaded.value || !welcomeSeen.value) return
    const tips = selectTips(view)
    if (tips.length === 0) return
    const shownKeys = await runTour(tips)
    if (shownKeys.length === 0) return
    state.value = await api.post<OnboardingState>('/onboarding/tips', {
      tip_keys: shownKeys,
    })
  }

  return {
    state: readonly(state),
    loaded: readonly(loaded),
    welcomeSeen,
    load,
    markWelcomeSeen,
    selectTips,
    startTour,
  }
}
