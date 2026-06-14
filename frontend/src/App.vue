<template>
  <v-app>
    <v-app-bar flat>
      <v-progress-linear
        v-if="isBusy"
        color="primary"
        indeterminate
        absolute
        location="bottom"
      />
      <MtButton
        variant="icon"
        tone="primary"
        icon="mdi-arrow-left"
        @click="router.back()"
      />

      <v-app-bar-title>
        <span class="brand">
          <v-icon class="brand__logo text-primary" size="22">mdi-dice-5</v-icon>
          <!-- Desktop: wordmark + context. Mobile: a single full-width,
               ellipsised line (context, or the brand when there is none)
               so the title never crops in the crowded bar. -->
          <template v-if="mdAndUp">
            <span class="brand__name">MeepleTime</span>
            <template v-if="title">
              <span class="brand__sep">·</span>
              <span class="brand__ctx">{{ title }}</span>
            </template>
          </template>
          <span v-else class="brand__ctx">{{ title || 'MeepleTime' }}</span>
        </span>
      </v-app-bar-title>

      <!-- No <v-spacer>: v-app-bar-title already flex-grows, so it fills
           the space up to the trailing actions. A spacer here would steal
           half that growth and clip the title on narrow (mobile) bars. -->

      <!-- Circle actions: inline icons on desktop; a single overflow
           menu on mobile to keep the bar uncrowded. -->
      <template v-if="mdAndUp">
        <MtButton
          v-for="action in actions"
          :key="action.label"
          variant="icon"
          tone="primary"
          :icon="action.icon"
          :title="action.label"
          class="mr-1"
          @click="action.action()"
        />
      </template>
      <v-menu v-else-if="actions.length">
        <template #activator="{ props }">
          <MtButton
            v-bind="props"
            variant="icon"
            tone="primary"
            icon="mdi-dots-vertical"
            title="More actions"
          />
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="action in actions"
            :key="action.label"
            :prepend-icon="action.icon"
            :title="action.label"
            @click="action.action()"
          />
        </v-list>
      </v-menu>

      <MtButton
        v-if="auth.isLoggedIn.value"
        variant="icon"
        tone="primary"
        icon="mdi-cog"
        title="Notification settings"
        class="hidden-sm-and-down"
        @click="router.push('/profile')"
      />

      <template v-if="auth.isLoggedIn.value">
        <v-avatar
          size="34"
          color="primary"
          class="app-avatar hidden-sm-and-down"
        >
          <span class="text-caption font-weight-bold">{{ userInitial }}</span>
        </v-avatar>
        <MtButton
          variant="icon"
          tone="primary"
          icon="mdi-logout"
          class="hidden-sm-and-down"
          @click="handleLogout"
        />
      </template>
    </v-app-bar>

    <AppNav />

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDisplay } from 'vuetify'
import { useAuth } from './composables/auth'
import { useAppBar } from './composables/appBar'
import { useRouter } from 'vue-router'
import { devAuth } from './config'
import { MtButton } from './ui'
import AppNav from './components/AppNav.vue'

const { title, actions, isBusy } = useAppBar()

const auth = useAuth()
const router = useRouter()
const { mdAndUp } = useDisplay()

onMounted(async () => {
  await auth.loadFromStorage()
})

const userInitial = computed<string>(() => {
  const name =
    auth.oidcUser.value?.profile?.name ??
    auth.oidcUser.value?.profile?.email ??
    ''
  return (name as string).charAt(0).toUpperCase() || '?'
})

/** Sign out the current user via OIDC. */
async function handleLogout(): Promise<void> {
  await auth.logout()
  // Keycloak logout is a full-page redirect; the dev path only clears
  // local state, so send the user back to the dev-login picker.
  if (devAuth) await router.replace('/login')
}
</script>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.brand__logo {
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
}

.brand__name {
  font-family: var(--v-font-family-display, sans-serif);
  font-weight: 600;
}

.brand__sep {
  opacity: 0.45;
}

.brand__ctx {
  font-weight: 500;
  opacity: 0.85;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-avatar {
  color: rgb(var(--v-theme-on-primary));
}
</style>
