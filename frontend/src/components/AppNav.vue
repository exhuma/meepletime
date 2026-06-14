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
          v-for="item in items"
          :key="item.key"
          :prepend-icon="item.icon"
          :title="item.label"
          :active="isActive(item.key)"
          @click="navigate(item.key)"
        />
      </v-list>
    </v-navigation-drawer>

    <v-bottom-navigation v-else :model-value="activeKey" grow>
      <v-btn
        v-for="item in items"
        :key="item.key"
        :value="item.key"
        @click="navigate(item.key)"
      >
        <v-icon>{{ item.icon }}</v-icon>
        {{ item.label }}
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

const items = [
  { key: 'circles', icon: 'mdi-account-group', label: 'Circles' },
  { key: 'calendar', icon: 'mdi-calendar-month', label: 'Calendar' },
  { key: 'profile', icon: 'mdi-account-circle', label: 'Profile' },
]

/** Return true when the current route belongs to the given destination. */
function isActive(key: string): boolean {
  const p = route.path
  if (key === 'profile') return p === '/profile' || p.startsWith('/profile')
  if (key === 'calendar') return p.startsWith('/circles/')
  return p === '/circles' // circles
}

/** Derived active key used as the bottom-navigation model-value. */
const activeKey = computed<string | null>(() => {
  for (const item of items) {
    if (isActive(item.key)) return item.key
  }
  return null
})

/** Route to the destination identified by key. */
function navigate(key: string): void {
  if (key === 'calendar') {
    const id = lastCircleId()
    router.push(id ? `/circles/${id}` : '/circles')
  } else if (key === 'profile') {
    router.push('/profile')
  } else {
    router.push('/circles')
  }
}
</script>
