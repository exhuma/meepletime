<template>
  <div>
    <v-container class="pa-3 pb-0" style="max-width: 720px">
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

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import { rememberCircle } from '../composables/lastCircle'

const route = useRoute()
const router = useRouter()
const circlesState = useCircles()

const circleId = route.params.id as string

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
.circle-title {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.1;
  margin-bottom: 0.5rem;
}
</style>
