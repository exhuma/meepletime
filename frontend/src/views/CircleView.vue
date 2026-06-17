<template>
  <!-- Two-column shell: the main column stacks the hero, tabs and the
       active child view (calendar/list) vertically, so they read as one
       group. The viable-days rail is a sibling column on the calendar
       tab, which keeps the header aligned with the calendar without a
       spacer hack. -->
  <div class="circle-shell">
    <div class="circle-main">
      <v-container class="pa-3 pb-0" style="max-width: 720px">
        <!-- Subtle hero banner: the circle photo (or brand-gradient
             fallback) fades into the page via a bottom scrim, with the
             circle name overlaid. Purely atmospheric, kept understated. -->
        <div
          class="circle-hero"
          :style="
            heroBackgroundStyle(circlesState.currentCircle.value?.image_ref)
          "
        >
          <div class="circle-hero__scrim" aria-hidden="true"></div>
          <h1 class="circle-title">
            {{ circlesState.currentCircle.value?.name || 'Loading…' }}
          </h1>
        </div>

        <!-- Calendar / List tab strip shared by both child views.
             Selection is driven by the active route; navigation happens
             on change. Binding :to instead would mark Calendar active on
             the nested /list route (prefix match). -->
        <v-tabs
          :model-value="activeTab"
          color="primary"
          density="comfortable"
          grow
          data-tour="circle-tabs"
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

      <router-view />
    </div>

    <CalendarSideRail
      v-if="mdAndUp && activeTab === 'calendar'"
      :circle-id="circleId"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useDisplay } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import { rememberCircle } from '../composables/lastCircle'
import { heroBackgroundStyle } from '../lib/circleImage'
import CalendarSideRail from '../components/CalendarSideRail.vue'

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
/* Centre the [main + rail] group. The main column holds the hero, tabs
   and the active child view stacked vertically; the rail sits beside it
   on the calendar tab. align-items:flex-start lets the rail pin to the
   top and run its own height. */
.circle-shell {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: var(--mt-rail-gap);
}

.circle-main {
  flex: 0 1 auto;
  min-width: 0;
}

.circle-hero {
  position: relative;
  height: 132px;
  margin-bottom: 0.75rem;
  border-radius: var(--mt-card-radius, 1rem);
  background-size: cover;
  background-position: center;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
}

/* Fade the photo into the page background so it reads as a quiet
   accent and keeps the overlaid title legible. */
.circle-hero__scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgb(var(--v-theme-background)) 0%,
    rgba(var(--v-theme-background), 0.55) 35%,
    rgba(var(--v-theme-background), 0) 100%
  );
}

.circle-title {
  position: relative;
  margin: 0;
  padding: 0 0.9rem 0.55rem;
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.1;
  color: rgb(var(--v-theme-on-background));
}
</style>
