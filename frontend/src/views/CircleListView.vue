<template>
  <v-container class="pa-3" style="max-width: 720px">
    <div v-if="rows.length === 0" class="list-empty">
      <v-icon size="40" class="mb-2">mdi-calendar-blank-outline</v-icon>
      <p class="text-body-2 text-medium-emphasis mb-0">
        {{
          viableOnly
            ? 'No upcoming viable days yet.'
            : 'No upcoming days with attendees yet.'
        }}
      </p>
    </div>

    <div v-else class="list-stack">
      <MtCard
        v-for="row in rows"
        :key="row.date"
        interactive
        :tone="row.viability.is_viable ? 'viable' : undefined"
        :to="`/circles/${circleId}/day/${row.date}`"
      >
        <div class="row-body">
          <div class="row-head">
            <div class="row-date">
              <span class="row-date__dow">{{
                safeFormat(row.date, 'EEE')
              }}</span>
              <span class="row-date__full">{{
                safeFormat(row.date, 'MMM d')
              }}</span>
            </div>
            <div class="row-markers">
              <v-chip size="x-small" color="attend" variant="tonal">
                {{ row.viability.attendee_count }} attending
              </v-chip>
              <v-chip
                v-if="row.viability.hosting_count > 0"
                size="x-small"
                color="host"
                variant="tonal"
              >
                <v-icon start size="12">mdi-home-variant</v-icon>
                {{ row.viability.hosting_count }}
              </v-chip>
              <v-chip
                v-if="row.viability.is_viable"
                size="x-small"
                color="viable"
                variant="flat"
              >
                Viable
              </v-chip>
              <v-chip
                v-if="row.viability.is_soft_max_exceeded"
                size="x-small"
                color="tertiary"
                variant="tonal"
              >
                Over soft max
              </v-chip>
              <v-chip
                v-if="row.viability.has_multiple_hosts_warning"
                size="x-small"
                color="tertiary"
                variant="text"
              >
                <v-icon start size="10">mdi-circle</v-icon>Multiple hosts
              </v-chip>
            </div>
          </div>
          <p class="row-people">{{ peopleFor(row) }}</p>
        </div>
      </MtCard>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { addMonths } from 'date-fns'
import { useCircles } from '../composables/circles'
import { useAppBar, useAppBarContext } from '../composables/appBar'
import { formatDate, buildUpcomingDays } from '../lib/calendar'
import type { UpcomingDay } from '../lib/calendar'
import { enrichAttendees } from '../lib/members'
import { safeFormat } from '../lib/datetime'
import { MtCard } from '../ui'

const route = useRoute()
const circlesState = useCircles()
const { startJob, endJob } = useAppBar()

const circleId = route.params.id as string
const viableOnly = ref(false)

const today = new Date()
const todayStr = formatDate(today)

useAppBarContext('Upcoming days', [
  {
    icon: 'mdi-filter-variant',
    label: 'Viable days only',
    action: () => (viableOnly.value = !viableOnly.value),
  },
])

/** Upcoming days with at least one attendee, honouring the filter. */
const rows = computed<UpcomingDay[]>(() =>
  buildUpcomingDays(circlesState.viability.value, todayStr, viableOnly.value),
)

/** Comma-separated attendee pseudonyms for a day row. */
function peopleFor(row: UpcomingDay): string {
  return enrichAttendees(
    row.viability.availabilities,
    circlesState.members.value,
  )
    .map((a) => a.pseudonym)
    .join(', ')
}

onMounted(async () => {
  startJob('load-upcoming')
  try {
    const start = todayStr
    const end = formatDate(addMonths(today, 3))
    await circlesState.fetchViability(circleId, start, end)
  } finally {
    endJob('load-upcoming')
  }
})
</script>

<style scoped>
.list-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: rgb(var(--v-theme-on-surface-variant));
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.row-body {
  padding: 0.85rem 1rem;
}

.row-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.row-date {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  flex: 0 0 auto;
}

.row-date__dow {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgb(var(--v-theme-on-surface-variant));
}

.row-date__full {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 1.15rem;
  font-weight: 600;
}

.row-markers {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  justify-content: flex-end;
}

.row-people {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface-variant));
}
</style>
