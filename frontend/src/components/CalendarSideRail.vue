<template>
  <!--
    Compact list of upcoming viable days for the current circle, shown
    beside the calendar on desktop. Reuses viability already fetched by
    the calendar view — it never triggers a network call of its own.
  -->
  <aside class="side-rail">
    <h2 class="side-rail__heading">Viable days</h2>

    <p v-if="rows.length === 0" class="side-rail__empty">No viable days yet.</p>

    <div v-else class="side-rail__list">
      <MtCard
        v-for="row in rows"
        :key="row.date"
        interactive
        tone="viable"
        :to="`/circles/${circleId}/day/${row.date}`"
      >
        <div class="side-rail__row">
          <span class="side-rail__date">{{
            safeFormat(row.date, 'EEE, MMM d')
          }}</span>
          <v-chip size="x-small" color="attend" variant="tonal">
            {{ row.viability.attendee_count }}
          </v-chip>
        </div>
      </MtCard>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useCircles } from '../composables/circles'
import { formatDate, buildUpcomingDays } from '../lib/calendar'
import type { UpcomingDay } from '../lib/calendar'
import { safeFormat } from '../lib/datetime'
import { MtCard } from '../ui'

defineProps<{
  /** Circle whose viable days are listed. */
  circleId: string
}>()

const circlesState = useCircles()
// Captured at mount — matches the calendar view's pattern; refresh on reload.
const todayStr = formatDate(new Date())

/** Upcoming viable days from already-fetched viability data. */
const rows = computed<UpcomingDay[]>(() =>
  buildUpcomingDays(circlesState.viability.value, todayStr, true),
)
</script>

<style scoped>
.side-rail {
  width: var(--mt-rail-width);
  flex: 0 0 var(--mt-rail-width);
  /* Stand as its own full-height column, pinned below the fixed app bar
     (64px is Vuetify's default v-app-bar height) and scrolling
     independently when the viable-days list is long. Content stays
     top-aligned via the flex-column list below. */
  position: sticky;
  top: calc(64px + 1rem);
  max-height: calc(100vh - 64px - 2rem);
  overflow-y: auto;
}

.side-rail__heading {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
}

.side-rail__empty {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface-variant));
  margin: 0;
}

.side-rail__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.side-rail__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
}

.side-rail__date {
  font-size: 0.9rem;
  font-weight: 500;
}
</style>
