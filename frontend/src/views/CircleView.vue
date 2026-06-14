<template>
  <div>
    <!-- On desktop the calendar tab shows a side rail, so the calendar
         column is group-centred to its left. Reserve a matching rail
         spacer here so the title/tabs centre on the same column; the
         list tab has no rail, so it stays plain-centred. -->
    <div class="head-layout">
      <v-container class="pa-3 pb-0 head-main" style="max-width: 720px">
        <h1 class="circle-title">
          {{ circlesState.currentCircle.value?.name || 'Loading…' }}
        </h1>

        <!-- Calendar / List tab strip shared by both child views.
             Selection is driven by the active route; navigation happens
             on change. Binding :to instead would mark Calendar active on
             the nested /list route (prefix match). -->
        <v-tabs
          :model-value="activeTab"
          color="primary"
          density="comfortable"
          grow
          @update:model-value="onTab"
        >
          <v-tab value="calendar">
            <v-icon start>mdi-calendar-month</v-icon>Calendar
          </v-tab>
          <v-tab value="list">
            <v-icon start>mdi-format-list-bulleted</v-icon>List
          </v-tab>
        </v-tabs>
      </v-container>

      <div
        v-if="mdAndUp && activeTab === 'calendar'"
        class="rail-spacer"
        aria-hidden="true"
      ></div>
    </div>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useDisplay } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import { rememberCircle } from '../composables/lastCircle'

const route = useRoute()
const router = useRouter()
const circlesState = useCircles()
const { mdAndUp } = useDisplay()

const circleId = route.params.id as string

// Refine the browser tab title to the real circle name once it loads,
// overriding the generic per-route title set by the router.
watch(
  () => circlesState.currentCircle.value?.name,
  (name) => {
    if (name) document.title = `${name} · MeepleTime`
  },
  { immediate: true },
)

/** Which tab is highlighted, derived from the active child route. */
const activeTab = computed<'calendar' | 'list'>(() =>
  route.path.endsWith('/list') ? 'list' : 'calendar',
)

/** Navigate to the child route for the selected tab. */
function onTab(value: unknown): void {
  const target =
    value === 'list' ? `/circles/${circleId}/list` : `/circles/${circleId}`
  if (route.path !== target) router.push(target)
}

// Circle and members are shared by both tabs, so the wrapper owns
// fetching them; each child view fetches its own date-window data.
onMounted(() => {
  rememberCircle(circleId)
  circlesState.fetchCircle(circleId)
  circlesState.fetchMembers(circleId)
})
</script>

<style scoped>
/* Mirror CircleCalendarView's .cal-layout so the title/tabs centre on
   the same column as the calendar grid (rail reserved on desktop). */
.head-layout {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: var(--mt-rail-gap);
}

.head-main {
  flex: 0 1 auto;
}

.rail-spacer {
  flex: 0 0 var(--mt-rail-width);
}

.circle-title {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.1;
  margin-bottom: 0.5rem;
}
</style>
