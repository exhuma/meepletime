<template>
  <div>
    <v-app-bar elevation="1" color="white">
      <v-btn icon @click="router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title class="text-truncate">
        {{ circles.currentCircle?.name || 'Loading...' }}
      </v-app-bar-title>
      <v-switch
        v-model="viableOnly"
        label="Viable only"
        color="primary"
        hide-details
        density="compact"
        class="mr-3"
        style="max-width:140px"
      />
    </v-app-bar>

    <v-container class="pa-2 pt-0" style="max-width:600px">
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />

      <div ref="listContainer">
        <template v-for="date in filteredDates" :key="date">
          <DayCell
            :date="date"
            :viability="circles.viability[date] || null"
            :myState="getMyState(date)"
            :attendees="circles.calendar[date] || []"
            @toggle="handleToggle(date)"
            @detail="router.push(`/circles/${circleId}/day/${date}`)"
          />
        </template>
      </div>

      <v-alert v-if="!loading && filteredDates.length === 0 && viableOnly" type="info" class="mt-4">
        No viable days found in this range.
      </v-alert>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { format, addDays, subMonths, addMonths } from 'date-fns'
import { useCirclesStore } from '../stores/circles'
import { useAuthStore } from '../stores/auth'
import DayCell from '../components/DayCell.vue'

const route = useRoute()
const router = useRouter()
const circles = useCirclesStore()
const auth = useAuthStore()

const circleId = route.params.id
const viableOnly = ref(false)
const loading = ref(false)
const listContainer = ref(null)
const todayStr = format(new Date(), 'yyyy-MM-dd')

const startDate = format(subMonths(new Date(), 1), 'yyyy-MM-dd')
const endDate = format(addMonths(new Date(), 2), 'yyyy-MM-dd')

function generateDateRange(start, end) {
  const dates = []
  let current = new Date(start + 'T00:00:00')
  const last = new Date(end + 'T00:00:00')
  while (current <= last) {
    dates.push(format(current, 'yyyy-MM-dd'))
    current = addDays(current, 1)
  }
  return dates
}

const allDates = generateDateRange(startDate, endDate)

const filteredDates = computed(() => {
  if (!viableOnly.value) return allDates
  return allDates.filter(d => circles.viability[d]?.is_viable)
})

function getMyState(date) {
  const userId = auth.user?.id
  const entries = circles.calendar[date] || []
  const mine = entries.find(a => a.user_id === userId)
  return mine?.state || 'empty'
}

async function handleToggle(date) {
  const current = getMyState(date)
  try {
    if (current === 'empty') {
      await circles.setAvailability(circleId, date, 'attending')
    } else if (current === 'attending') {
      await circles.setAvailability(circleId, date, 'hosting')
    } else {
      await circles.deleteAvailability(circleId, date, auth.user?.id)
    }
  } catch (e) {
    console.error('Toggle error', e)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      circles.fetchCircle(circleId),
      circles.fetchMembers(circleId),
      circles.fetchCalendar(circleId, startDate, endDate),
      circles.fetchViability(circleId, startDate, endDate),
    ])
  } finally {
    loading.value = false
  }

  await nextTick()
  if (listContainer.value) {
    const todayEl = listContainer.value.querySelector(`[data-date="${todayStr}"]`)
    if (todayEl) {
      todayEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
})
</script>
