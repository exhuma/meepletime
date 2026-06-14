<template>
  <div>
    <div class="cal-layout">
      <v-container class="pa-3 cal-main" style="max-width: 720px">
        <!-- Month navigation -->
        <div class="cal-nav">
          <span class="cal-nav__label">{{ monthLabel }}</span>
          <div class="cal-nav__arrows">
            <MtButton
              variant="icon"
              tone="primary"
              icon="mdi-chevron-left"
              :disabled="!canGoPrev"
              @click="prevMonth"
            />
            <MtButton
              variant="icon"
              tone="primary"
              icon="mdi-chevron-right"
              @click="nextMonth"
            />
          </div>
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
            class="calendar-blank"
          ></div>

          <!-- Day cells -->
          <CalendarDayCell
            v-for="day in daysInMonth"
            :key="day.date"
            :date="day.date"
            :day-of-month="day.dayOfMonth"
            :my-state="day.myState"
            :viability="day.viability"
            :is-today="day.date === todayStr"
            :is-past="day.date < todayStr"
            :dimmed="viableOnly && !day.viability?.is_viable"
            @activate="onActivate"
            @context="onContext"
          />
        </div>

        <!-- Legend -->
        <div class="d-flex flex-wrap ga-2 px-2 py-3">
          <v-chip size="x-small" color="attend" variant="tonal">
            <v-icon start size="12" color="attend">mdi-check-circle</v-icon
            >Attending
          </v-chip>
          <v-chip size="x-small" color="host" variant="tonal">
            <v-icon start size="12">mdi-home-variant</v-icon>Hosting
          </v-chip>
          <v-chip size="x-small" color="viable" variant="flat"
            >Viable day</v-chip
          >
          <v-chip size="x-small" color="tertiary" variant="tonal"
            >Over soft max</v-chip
          >
          <v-chip size="x-small" color="tertiary" variant="text">
            <v-icon start size="10">mdi-circle</v-icon>Multiple hosts
          </v-chip>
        </div>

        <p
          class="text-caption text-medium-emphasis text-center mt-1 d-flex align-center justify-center"
        >
          <v-icon size="14" class="mr-1">mdi-gesture-tap-hold</v-icon>
          Tap a day to set availability · long-press or right-click for options
        </p>
      </v-container>

      <CalendarSideRail v-if="mdAndUp" :circle-id="circleId" />
    </div>

    <!-- Invite / QR Code dialog -->
    <InviteDialog
      v-if="circlesState.currentCircle.value"
      v-model="inviteDialog"
      :circle="circlesState.currentCircle.value"
      :is-admin="isAdminOrOwner"
      @regenerated="onInviteRegenerated"
    />

    <CircleNotificationsDialog
      v-if="circlesState.currentCircle.value"
      v-model="notificationsDialog"
      :circle-id="circleId"
      :circle-name="circlesState.currentCircle.value.name"
      :is-admin="isAdminOrOwner"
    />

    <DayContextSheet
      v-model="contextSheetOpen"
      :date="selectedDay ?? ''"
      :is-past="(selectedDay ?? '') < todayStr"
      :presence-state="selectedDayState"
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
import { useDisplay } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { addMonths, startOfMonth } from 'date-fns'
import { useCircles } from '../composables/circles'
import { useAuth } from '../composables/auth'
import InviteDialog from '../components/InviteDialog.vue'
import CircleNotificationsDialog from '../components/CircleNotificationsDialog.vue'
import DayContextSheet from '../components/DayContextSheet.vue'
import ConstraintEditorDialog from '../components/ConstraintEditorDialog.vue'
import CalendarDayCell from '../components/CalendarDayCell.vue'
import CalendarSideRail from '../components/CalendarSideRail.vue'
import { MtButton } from '../ui'
import {
  formatDate,
  monthLabel as monthLabelFor,
  firstDayOffset as firstDayOffsetFor,
  canGoToPrevMonth,
  buildMonthDays,
} from '../lib/calendar'
import {
  isAdminOrOwner as computeIsAdminOrOwner,
  myState,
} from '../lib/members'
import { useAppBar, useAppBarContext } from '../composables/appBar'

useAppBarContext('Circle Calendar', [
  {
    icon: 'mdi-qrcode',
    label: 'Invite / QR Code',
    action: () => (inviteDialog.value = true),
  },
  {
    icon: 'mdi-bell-cog',
    label: 'Notification settings',
    action: () => (notificationsDialog.value = true),
  },
  {
    icon: 'mdi-filter-variant',
    label: 'Viable days only',
    action: () => (viableOnly.value = !viableOnly.value),
  },
])

const route = useRoute()
const router = useRouter()
const circlesState = useCircles()
const auth = useAuth()
const { mdAndUp } = useDisplay()
const { startJob, endJob } = useAppBar()

const circleId = route.params.id as string
const viableOnly = ref(false)
const inviteDialog = ref(false)
const notificationsDialog = ref(false)
const selectedDay = ref<string | null>(null)
const contextSheetOpen = ref(false)
const constraintDialogOpen = ref(false)

const today = new Date()
const todayStr = formatDate(today)

// Start at current month; do not allow navigating to past months
const currentMonthStart = ref(startOfMonth(today))

const monthLabel = computed<string>(() =>
  monthLabelFor(currentMonthStart.value),
)

const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

/** Offset of the first day (0 = Sunday). */
const firstDayOffset = computed<number>(() =>
  firstDayOffsetFor(currentMonthStart.value),
)

/** Build the array of day cells for the current month. */
const daysInMonth = computed(() =>
  buildMonthDays(
    currentMonthStart.value,
    circlesState.calendar.value,
    circlesState.viability.value,
    auth.userId.value,
  ),
)

/** True when navigating back would go before the current month. */
const canGoPrev = computed<boolean>(() =>
  canGoToPrevMonth(currentMonthStart.value, today),
)

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
  const start = formatDate(currentMonthStart.value)
  const end = formatDate(addMonths(currentMonthStart.value, 1))
  await Promise.all([
    circlesState.fetchCalendar(circleId, start, end),
    circlesState.fetchViability(circleId, start, end),
  ])
}

/** True if the current user is an owner or admin of this circle. */
const isAdminOrOwner = computed<boolean>(() =>
  computeIsAdminOrOwner(circlesState.members.value, auth.userId.value),
)

/** The current user's presence state for the selected day. */
const selectedDayState = computed<'attending' | 'hosting' | null>(() => {
  if (!selectedDay.value) return null
  const entries = circlesState.calendar.value[selectedDay.value] ?? []
  return myState(entries, auth.userId.value)
})

/**
 * Primary tap: cycle the user's presence for a future day. Past days
 * are read-only, so taps on them are ignored (use the context menu).
 */
async function onActivate(date: string): Promise<void> {
  if (date < todayStr) return
  await cycleAvailability(date)
}

/**
 * Long-press / right-click: open the day context sheet for any day
 * (past days open in read-only form).
 */
function onContext(date: string): void {
  selectedDay.value = date
  contextSheetOpen.value = true
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
  startJob('load-circles')
  try {
    const start = formatDate(currentMonthStart.value)
    const end = formatDate(addMonths(currentMonthStart.value, 3))
    // Circle + members are fetched by the parent CircleView shell.
    await Promise.all([
      circlesState.fetchCalendar(circleId, start, end),
      circlesState.fetchViability(circleId, start, end),
    ])
  } finally {
    endJob('load-circles')
  }
})
</script>

<style scoped>
/*
 * On desktop the calendar and its side rail sit in one centred row;
 * the v-container keeps its own max-width and the rail takes a fixed
 * column to its right. Below md the rail is not rendered, so this
 * collapses to the single calendar column unchanged.
 */
.cal-layout {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 1.5rem;
}

.cal-main {
  flex: 0 1 auto;
}

.cal-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0 1rem;
}

.cal-nav__label {
  flex: 1 1 auto;
  font-family: var(--v-font-family-display);
  font-size: 1.9rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.cal-nav__arrows {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  background: transparent;
}

.calendar-header {
  background: transparent;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 6px 2px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.calendar-blank {
  background: transparent;
}
</style>
