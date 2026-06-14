<template>
  <v-container class="pa-4" style="max-width: 640px">
    <div class="welcome-hero text-center mb-6">
      <v-icon size="72" color="primary">mdi-dice-5</v-icon>
      <h1 class="welcome-title mt-3">Welcome to MeepleTime</h1>
      <p class="text-body-1 text-medium-emphasis mb-0">
        A low-overhead way for a small circle of friends to find days that work
        for everyone to meet up.
      </p>
    </div>

    <MtCard class="pa-5 mb-4">
      <h2 class="welcome-h2 mb-2">What it is</h2>
      <p class="text-body-2 mb-0">
        A <strong>circle</strong> is a private group of friends sharing a
        calendar. On each day, members mark whether they
        <strong>can attend</strong> or <strong>can host</strong>, and the app
        works out which days are viable meetups based on the circle's rules.
        Circles are invite-only — you only ever see the ones you've been invited
        to.
      </p>
    </MtCard>

    <MtCard class="pa-5 mb-4">
      <h2 class="welcome-h2 mb-3">How to use it</h2>
      <ol class="welcome-steps">
        <li>
          <strong>Join or create a circle.</strong> Open an invite link, or
          create your own and invite others.
        </li>
        <li>
          <strong>Tap a day</strong> to cycle your availability:
          <span class="welcome-cycle">
            empty → attending → hosting → empty </span
          >. Changes save instantly.
        </li>
        <li>
          <strong>Watch the markers.</strong> A day becomes a possible meetup
          once at least one member is in. Viable days are highlighted.
        </li>
        <li>
          Switch between the <strong>Calendar</strong> and
          <strong>List</strong> tabs — the List is the quickest way to see when
          you can meet.
        </li>
      </ol>
    </MtCard>

    <p class="text-caption text-medium-emphasis text-center mb-5">
      Short tips will point out key features as you go — only a few at a time,
      so nothing feels overwhelming.
    </p>

    <MtButton
      tone="primary"
      size="x-large"
      block
      icon="mdi-rocket-launch-outline"
      :loading="finishing"
      @click="getStarted"
    >
      Get started
    </MtButton>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { MtButton, MtCard } from '../ui'
import { useOnboarding } from '../composables/useOnboarding'

const router = useRouter()
const onboarding = useOnboarding()
const finishing = ref(false)

/** Mark the welcome intro as seen, then head to the circles list. */
async function getStarted(): Promise<void> {
  finishing.value = true
  try {
    await onboarding.markWelcomeSeen()
  } catch (e) {
    // Don't trap the user on the welcome screen if the save fails;
    // the worst case is the intro shows again next session.
    console.error('[onboarding] Failed to mark welcome seen:', e)
  } finally {
    finishing.value = false
  }
  await router.replace('/circles')
}
</script>

<style scoped>
.welcome-title {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-size: 1.9rem;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 0.5rem;
}

.welcome-h2 {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-size: 1.2rem;
  font-weight: 600;
}

.welcome-steps {
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  font-size: 0.9rem;
}

.welcome-cycle {
  font-family: var(--v-font-family-mono, monospace);
  font-size: 0.82rem;
  white-space: nowrap;
}
</style>
