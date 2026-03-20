<template>
  <div :data-date="date">
    <v-card
      class="mb-2 day-cell"
      :style="{ opacity: isPast ? 0.6 : 1 }"
      elevation="1"
      rounded="lg"
    >
      <div class="d-flex align-stretch">
        <!-- Color stripe -->
        <div
          class="flex-shrink-0"
          :style="{ width: '6px', borderRadius: '8px 0 0 8px', backgroundColor: stripeColor }"
        />

        <!-- Main content (clickable for toggle) -->
        <div
          class="flex-grow-1 pa-3 d-flex align-center"
          style="cursor: pointer; min-width: 0;"
          @click="!isPast && $emit('toggle')"
        >
          <!-- Date info -->
          <div class="mr-3 text-center" style="min-width:44px">
            <div class="text-caption text-grey-darken-1 font-weight-medium">{{ dayName }}</div>
            <div class="text-h6 font-weight-bold" style="line-height:1.1">{{ dayNumber }}</div>
            <div class="text-caption text-grey">{{ monthName }}</div>
          </div>

          <!-- Center info -->
          <div class="flex-grow-1">
            <div class="d-flex align-center flex-wrap gap-1 mb-1">
              <v-chip
                size="x-small"
                :color="stateColor"
                :variant="myState === 'empty' ? 'outlined' : 'tonal'"
                class="text-capitalize"
              >
                {{ myState === 'empty' ? 'Tap to attend' : myState }}
              </v-chip>

              <v-icon
                v-if="viability?.is_viable"
                color="green"
                size="16"
                title="Viable day"
              >mdi-circle</v-icon>

              <v-icon
                v-if="viability?.is_soft_max_exceeded"
                color="orange"
                size="16"
                title="Over soft max"
              >mdi-alert</v-icon>

              <v-icon
                v-if="viability?.has_multiple_hosts_warning"
                color="blue"
                size="16"
                title="Multiple hosts"
              >mdi-home-group</v-icon>
            </div>

            <div v-if="attendees.length > 0" class="d-flex align-center">
              <v-icon size="14" color="grey" class="mr-1">mdi-account-multiple</v-icon>
              <span class="text-caption text-grey">{{ attendees.length }} attending</span>
            </div>
          </div>
        </div>

        <!-- Detail chevron -->
        <v-btn
          icon
          variant="text"
          size="small"
          @click.stop="$emit('detail')"
          class="align-self-center mr-1"
        >
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { format, parseISO, isBefore, startOfDay } from 'date-fns'
import type { DayViability } from '../types'

const props = defineProps<{
  date: string
  viability?: DayViability | null
  myState?: string
  attendees?: unknown[]
}>()

defineEmits(['toggle', 'detail'])

const parsedDate = computed(() => {
  try { return parseISO(props.date) } catch { return new Date() }
})

const dayName = computed(() => format(parsedDate.value, 'EEE'))
const dayNumber = computed(() => format(parsedDate.value, 'd'))
const monthName = computed(() => format(parsedDate.value, 'MMM'))

const isPast = computed(() => isBefore(parsedDate.value, startOfDay(new Date())))

const myState = computed(() => props.myState ?? 'empty')
const attendees = computed(() => props.attendees ?? [])

const stripeColor = computed(() => {
  if (myState.value === 'hosting') return '#4CAF50'
  if (myState.value === 'attending') return '#2196F3'
  return '#E0E0E0'
})

const stateColor = computed(() => {
  if (myState.value === 'hosting') return 'green'
  if (myState.value === 'attending') return 'blue'
  return 'grey'
})
</script>

<style scoped>
.day-cell {
  transition: transform 0.1s, box-shadow 0.1s;
}
.day-cell:active {
  transform: scale(0.99);
}
</style>
