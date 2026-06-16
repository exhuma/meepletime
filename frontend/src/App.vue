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
        <!-- bg-color overrides the app-wide `VList: bgColor: transparent`
             default (theme); a floating menu needs an opaque surface so
             the page does not show through it. -->
        <v-list density="compact" bg-color="surface" elevation="8">
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
        icon="mdi-help-circle-outline"
        title="Help / Welcome"
        @click="router.push('/welcome')"
      />

      <!-- Single account entry-point: the avatar opens a menu with the
           profile page and sign-out, so account actions are no longer
           spread across ambiguous icon buttons. -->
      <v-menu v-if="auth.isLoggedIn.value">
        <template #activator="{ props }">
          <v-avatar
            v-bind="props"
            size="34"
            color="primary"
            class="app-avatar"
            role="button"
            title="Account"
          >
            <v-img
              v-if="avatarUrl && !avatarError"
              :src="avatarUrl"
              alt="Your profile picture"
              @error="avatarError = true"
            />
            <span v-else class="text-caption font-weight-bold">{{
              userInitial
            }}</span>
          </v-avatar>
        </template>
        <!-- Opaque surface so the page does not show through the menu
             (the app-wide VList bgColor default is transparent). -->
        <v-list density="compact" bg-color="surface" elevation="8">
          <v-list-item
            prepend-icon="mdi-account-circle"
            title="Profile"
            @click="router.push('/profile')"
          />
          <v-list-item
            prepend-icon="mdi-logout"
            title="Log out"
            @click="handleLogout"
          />
        </v-list>
      </v-menu>
    </v-app-bar>

    <AppNav />

    <v-main>
      <router-view />
      <AppFooter />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useDisplay } from 'vuetify'
import { useAuth } from './composables/auth'
import { useAppBar } from './composables/appBar'
import { useRouter } from 'vue-router'
import { devAuth } from './config'
import { resolveImageUrl } from './lib/circleImage'
import { MtButton } from './ui'
import AppNav from './components/AppNav.vue'
import AppFooter from './components/AppFooter.vue'

const { title, actions, isBusy } = useAppBar()

const auth = useAuth()
const router = useRouter()
const { mdAndUp } = useDisplay()

// Restore any persisted OIDC session so the app bar (avatar, actions)
// reflects auth state on a fresh page load. The welcome/onboarding gate
// now lives in the router guard (router/index.ts) so it fires reliably
// on first login, regardless of when the session is established.
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

// Resolved avatar (uploaded image, provider photo, or gravatar). The
// gravatar fallback 404s when none exists, so fall back to initials on
// any image load error; reset the flag whenever the source changes.
const avatarUrl = computed<string | null>(() =>
  resolveImageUrl(auth.avatarRef.value),
)
const avatarError = ref(false)
watch(avatarUrl, () => {
  avatarError.value = false
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
  cursor: pointer;
}
</style>
