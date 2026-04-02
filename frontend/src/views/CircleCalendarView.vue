<template>
  <div>
    <v-app-bar elevation="1" color="surface">
      <v-btn icon @click="router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title class="text-truncate">
        {{ circlesState.currentCircle.value?.name || 'Loading...' }}
      </v-app-bar-title>
      <v-btn
        icon
        :color="viableOnly ? 'primary' : undefined"
        title="Viable days only"
        @click="viableOnly = !viableOnly"
      >
        <v-icon>mdi-filter-variant</v-icon>
      </v-btn>
      <v-btn-toggle
        v-model="calendarMode"
        mandatory
        density="compact"
        class="mx-1"
      >
        <v-btn value="availability" icon title="Availability mode">
          <v-icon>mdi-calendar-check</v-icon>
        </v-btn>
        <v-btn value="select" icon title="Select mode">
          <v-icon>mdi-cursor-default-click</v-icon>
        </v-btn>
      </v-btn-toggle>
      <v-btn
        icon
        :title="'Invite / QR Code'"
        @click="inviteDialog = true"
        class="mr-1"
      >
        <v-icon>mdi-qrcode</v-icon>
      </v-btn>
    </v-app-bar>

    <v-container class="pa-2" style="max-width: 700px">
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        class="mb-2"
      />

      <!-- Month navigation -->
      <div class="d-flex align-center px-2 py-2">
        <v-btn icon variant="text" :disabled="!canGoPrev" @click="prevMonth">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <span class="flex-grow-1 text-center text-subtitle-1 font-weight-bold">
          {{ monthLabel }}
        </span>
        <v-btn icon variant="text" @click="nextMonth">
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
      </div>

      <!-- Calendar grid -->
      <div class="calendar-grid">
        <!-- Day headers -->
        <div class="calendar-header" v-for="day in dayHeaders" :key="day">
          {{ day }}
        </div>

        <!-- Blank cells for first week offset -->
        <div
          v-for="n in firstDayOffset"
          :key="`blank-${n}`"
          class="calendar-cell calendar-cell--blank"
        ></div>

        <!-- Day cells -->
        <div
          v-for="day in daysInMonth"
          :key="day.date"
          class="calendar-cell"
          :class="{
            'calendar-cell--today': day.date === todayStr,
            'calendar-cell--past': day.date < todayStr,
            'calendar-cell--future':
              day.date >= todayStr || calendarMode === 'select',
            'calendar-cell--viable':
              day.viability?.is_viable && !day.viability.is_soft_max_exceeded,
            'calendar-cell--over-soft-max': day.viability?.is_soft_max_exceeded,
            'calendar-cell--hidden': viableOnly && !day.viability?.is_viable,
          }"
          @click="handleDayClick(day.date)"
        >
          <div class="calendar-cell__date">{{ day.dayOfMonth }}</div>
          <div
            v-if="day.myState"
            class="calendar-cell__chip"
            :class="`chip--${day.myState}`"
          >
            {{ day.myState === 'hosting' ? '🏠' : '✓' }}
          </div>
          <div
            v-if="day.viability && day.viability.attendee_count > 0"
            class="calendar-cell__count"
          >
            {{ day.viability.attendee_count }}
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="d-flex flex-wrap gap-2 px-2 py-3">
        <v-chip size="x-small" color="secondary" variant="tonal"
          >✓ Attending</v-chip
        >
        <v-chip size="x-small" color="primary" variant="tonal"
          >🏠 Hosting</v-chip
        >
        <v-chip size="x-small" color="primary" variant="flat"
          >Viable day</v-chip
        >
        <v-chip size="x-small" color="tertiary" variant="tonal"
          >Over soft max</v-chip
        >
      </div>

      <p class="text-caption text-medium-emphasis text-center mt-1">
        {{
          calendarMode === 'availability'
            ? 'Tap a future date to cycle your availability'
            : 'Tap a date for options'
        }}
      </p>
    </v-container>

    <!-- Invite / QR Code dialog -->
    <InviteDialog
      v-if="circlesState.currentCircle.value"
      v-model="inviteDialog"
      :circle="circlesState.currentCircle.value"
      :is-admin="isAdminOrOwner"
      @regenerated="onInviteRegenerated"
    />

    <DayContextSheet
      v-model="contextSheetOpen"
      :date="selectedDay ?? ''"
      :is-past="(selectedDay ?? '') < todayStr"
      :can-host="canHostDefault"
      @view-details="goToDetail"
      @edit-constraints="openConstraintEditor"
    />

    <ConstraintEditorDialog
      v-if="circlesState.currentCircle.value"
      v-model="constraintDialogOpen"
      :circle-id="circleId"
      :date="selectedDay ?? ''"
      :circle="circlesState.currentCircle.value"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  format,
  addMonths,
  startOfMonth,
  getDaysInMonth,
  getDay,
} from 'date-fns'
import { useCircles } from '../composables/circles'
import { useAuth } from '../composables/auth'
import InviteDialog from '../components/InviteDialog.vue'
import DayContextSheet from '../components/DayContextSheet.vue'
import ConstraintEditorDialog from '../components/ConstraintEditorDialog.vue'
import type { DayViability } from '../types'

const route = useRoute()
const router = useRouter()
const circlesState = useCircles()
const auth = useAuth()

const circleId = route.params.id as string
const viableOnly = ref(false)
const loading = ref(false)
const inviteDialog = ref(false)
const calendarMode = ref<'availability' | 'select'>('availability')
const selectedDay = ref<string | null>(null)
const contextSheetOpen = ref(false)
const constraintDialogOpen = ref(false)

const today = new Date()
const todayStr = format(today, 'yyyy-MM-dd')

// Start at current month; do not allow navigating to past months
const currentMonthStart = ref(startOfMonth(today))

const monthLabel = computed<string>(() =>
  format(currentMonthStart.value, 'MMMM yyyy'),
)

const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

/** Offset of the first day (0 = Sunday). */
const firstDayOffset = computed<number>(() => getDay(currentMonthStart.value))

interface DayCell {
  date: string
  dayOfMonth: number
  myState: 'attending' | 'hosting' | null
  viability: DayViability | null
}

/** Build the array of day cells for the current month. */
const daysInMonth = computed<DayCell[]>(() => {
  const count = getDaysInMonth(currentMonthStart.value)
  const userId = auth.userId.value
  const cells: DayCell[] = []
  for (let d = 1; d <= count; d++) {
    const date = format(
      new Date(
        currentMonthStart.value.getFullYear(),
        currentMonthStart.value.getMonth(),
        d,
      ),
      'yyyy-MM-dd',
    )
    const entries = circlesState.calendar.value[date] ?? []
    const mine = userId ? entries.find((a) => a.user_id === userId) : undefined
    const viab = circlesState.viability.value[date] ?? null
    cells.push({
      date,
      dayOfMonth: d,
      myState: mine?.state ?? null,
      viability: viab,
    })
  }
  return cells
})

/** True when navigating back would go before the current month. */
const canGoPrev = computed<boolean>(() => {
  const prevMonth = addMonths(currentMonthStart.value, -1)
  return prevMonth >= startOfMonth(today)
})

/** Navigate the calendar one month back, stopping at the current month. */
function prevMonth(): void {
  if (!canGoPrev.value) return
  currentMonthStart.value = addMonths(currentMonthStart.value, -1)
  reloadMonth()
}

/** Navigate the calendar one month forward. */
function nextMonth(): void {
  currentMonthStart.value = addMonths(currentMonthStart.value, 1)
  reloadMonth()
}

/** Fetch availability and viability data for the currently displayed month. */
async function reloadMonth(): Promise<void> {
  const start = format(currentMonthStart.value, 'yyyy-MM-dd')
  const end = format(addMonths(currentMonthStart.value, 1), 'yyyy-MM-dd')
  await Promise.all([
    circlesState.fetchCalendar(circleId, start, end),
    circlesState.fetchViability(circleId, start, end),
  ])
}

/** True if the current user is an owner or admin of this circle. */
const isAdminOrOwner = computed<boolean>(() => {
  const userId = auth.userId.value
  if (!userId) return false
  const member = circlesState.members.value.find((m) => m.user_id === userId)
  return member?.role === 'owner' || member?.role === 'admin'
})

/** True if the current user is a default host in this circle. */
const canHostDefault = computed<boolean>(() => {
  const userId = auth.userId.value
  if (!userId) return false
  const member = circlesState.members.value.find((m) => m.user_id === userId)
  return member?.can_host_default ?? false
})

/**
 * Handle a day cell click.
 *
 * Availability mode: cycle the user's presence for a future day.
 * Select mode: open the context sheet for any day (past = read-only).
 */
async function handleDayClick(date: string): Promise<void> {
  if (calendarMode.value === 'availability') {
    if (date < todayStr) return
    await cycleAvailability(date)
  } else {
    selectedDay.value = date
    contextSheetOpen.value = true
  }
}

/**
 * Cycle the current user's availability state for date:
 * empty → attending → hosting → empty
 */
async function cycleAvailability(date: string): Promise<void> {
  const userId = auth.userId.value
  if (!userId) return
  try {
    await circlesState.cycleAvailability(circleId, date, userId)
    await circlesState.fetchViability(circleId, date, date)
  } catch (e) {
    console.error('Availability cycle error', e)
  }
}

/** Navigate to the day detail view and close the context sheet. */
function goToDetail(): void {
  contextSheetOpen.value = false
  if (!selectedDay.value) return
  router.push(`/circles/${circleId}/day/${selectedDay.value}`)
}

/** Close the context sheet and open the constraint editor. */
function openConstraintEditor(): void {
  contextSheetOpen.value = false
  constraintDialogOpen.value = true
}

/** Refresh circle data after invite token regeneration. */
function onInviteRegenerated(): void {
  circlesState.fetchCircle(circleId)
}

onMounted(async () => {
  loading.value = true
  try {
    const start = format(currentMonthStart.value, 'yyyy-MM-dd')
    const end = format(addMonths(currentMonthStart.value, 3), 'yyyy-MM-dd')
    await Promise.all([
      circlesState.fetchCircle(circleId),
      circlesState.fetchMembers(circleId),
      circlesState.fetchCalendar(circleId, start, end),
      circlesState.fetchViability(circleId, start, end),
    ])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  background: rgb(var(--v-theme-outline-variant));
  border: 1px solid rgb(var(--v-theme-outline-variant));
  border-radius: 8px;
  overflow: hidden;
}

.calendar-header {
  background: rgb(var(--v-theme-surface-container-low));
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 6px 2px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.calendar-cell {
  background: rgb(var(--v-theme-surface));
  min-height: 72px;
  padding: 4px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  cursor: default;
  position: relative;
}

.calendar-cell--blank {
  background: rgb(var(--v-theme-surface-container-lowest));
  cursor: default;
}

.calendar-cell--past {
  background: rgb(var(--v-theme-surface-container-lowest));
  opacity: 0.5;
}

.calendar-cell--future {
  cursor: pointer;
}

.calendar-cell--future:hover {
  background: rgb(var(--v-theme-surface-container));
}

.calendar-cell--today {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -2px;
}

.calendar-cell--viable {
  background: rgb(var(--v-theme-primary-container));
}

.calendar-cell--over-soft-max {
  background: rgb(var(--v-theme-tertiary-container));
}

.calendar-cell--hidden {
  visibility: hidden;
}

.calendar-cell__date {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.calendar-cell__chip {
  font-size: 0.9rem;
  margin-top: 2px;
}

.chip--attending {
  color: rgb(var(--v-theme-secondary));
}

.chip--hosting {
  color: rgb(var(--v-theme-primary));
}

.calendar-cell__count {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface-variant));
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 4px;
  padding: 1px 4px;
}
</style>
