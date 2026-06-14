<template>
  <!--
    Global navigation. Renders nothing for logged-out users or on the
    auth screens; otherwise a slim left rail on desktop and a bottom
    navigation bar on smaller screens. Both live inside <v-app>, so
    Vuetify's layout system offsets <v-main> automatically — the rail
    pushes content right and the bottom bar reserves space below.
  -->
  <template v-if="visible">
    <v-navigation-drawer v-if="mdAndUp" rail permanent>
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-account-group"
          title="Circles"
          :active="active === 'circles'"
          @click="goCircles"
        />
        <v-list-item
          prepend-icon="mdi-calendar-month"
          title="Calendar"
          :active="active === 'calendar'"
          @click="goCalendar"
        />
        <v-list-item
          prepend-icon="mdi-account-circle"
          title="Profile"
          :active="active === 'profile'"
          @click="goProfile"
        />
      </v-list>
    </v-navigation-drawer>

    <v-bottom-navigation v-else :model-value="active" grow>
      <v-btn value="circles" @click="goCircles">
        <v-icon>mdi-account-group</v-icon>
        Circles
      </v-btn>
      <v-btn value="calendar" @click="goCalendar">
        <v-icon>mdi-calendar-month</v-icon>
        Calendar
      </v-btn>
      <v-btn value="profile" @click="goProfile">
        <v-icon>mdi-account-circle</v-icon>
        Profile
      </v-btn>
    </v-bottom-navigation>
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDisplay } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'
import { lastCircleId } from '../composables/lastCircle'

const { mdAndUp } = useDisplay()
const route = useRoute()
const router = useRouter()
const auth = useAuth()

/** Hide the nav while logged out or on the auth screens. */
const visible = computed<boolean>(
  () =>
    auth.isLoggedIn.value &&
    route.path !== '/login' &&
    route.path !== '/auth/callback',
)

/** Which destination the current route maps to, for active styling. */
const active = computed<'circles' | 'calendar' | 'profile' | null>(() => {
  const p = route.path
  if (p === '/profile') return 'profile'
  if (p === '/circles') return 'circles'
  if (p.startsWith('/circles/')) return 'calendar'
  return null
})

/** Open the circles list. */
function goCircles(): void {
  router.push('/circles')
}

/** Open the last viewed circle's calendar, or the list as a fallback. */
function goCalendar(): void {
  const id = lastCircleId()
  router.push(id ? `/circles/${id}` : '/circles')
}

/** Open profile settings. */
function goProfile(): void {
  router.push('/profile')
}
</script>
