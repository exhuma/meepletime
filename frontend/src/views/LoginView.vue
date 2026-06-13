<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" md="4" class="text-center">
        <div class="login-meeple text-primary"><MtMeeple /></div>
        <h1 class="login-title">MeepleTime</h1>
        <!-- Dev-only login (no Keycloak). DevLoginPanel is lazy
             behind a static import.meta.env.DEV guard, so Rollup
             drops it (and its /auth/dev calls) from prod builds. -->
        <component
          :is="DevLoginPanel"
          v-if="devAuth && DevLoginPanel"
          :return-to="returnTo"
        />
        <template v-else-if="!authError">
          <v-progress-circular
            indeterminate
            color="primary"
            size="40"
            class="mt-5"
          />
          <p class="mt-4 text-medium-emphasis">Redirecting to sign in…</p>
        </template>
        <template v-else>
          <v-alert type="error" class="my-4 text-left">
            Sign-in could not be completed. The server rejected the session —
            this usually happens after the identity provider was restarted.
          </v-alert>
          <MtButton tone="primary" size="large" @click="retrySignIn">
            Sign in again
          </MtButton>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'
import { userManager } from '../auth/oidc'
import { clearReauthGuard, hasAuthError } from '../auth/reauthGuard'
import { devAuth } from '../config'
import { MtButton } from '../ui'
import MtMeeple from '../ui/MtMeeple.vue'

// Dev-only picker. The static import.meta.env.DEV guard folds to
// `false` in any production build, so the dynamic import lives in
// dead code and Rollup never emits the DevLoginPanel chunk.
const DevLoginPanel = import.meta.env.DEV
  ? defineAsyncComponent(() => import('./DevLoginPanel.vue'))
  : null

const auth = useAuth()
const route = useRoute()
const router = useRouter()

const returnTo = (route.query.returnTo as string) ?? '/'
const authError = ref(false)

onMounted(async () => {
  // Already authenticated? Navigating to /login should just continue
  // to the destination (applies to both Keycloak and dev sessions).
  const existing = await userManager.getUser()
  if (existing && !existing.expired) {
    await router.replace(returnTo)
    return
  }
  if (devAuth) {
    // Dev mode: DevLoginPanel renders the preset picker instead of
    // redirecting to an identity provider that is not running.
    return
  }
  // After repeated 401s on freshly issued tokens the loop breaker lands
  // us here; do not auto-redirect (that is what would loop). Offer a
  // manual retry instead.
  if (hasAuthError()) {
    authError.value = true
    return
  }
  await auth.login(returnTo)
})

async function retrySignIn(): Promise<void> {
  clearReauthGuard()
  authError.value = false
  await auth.login(returnTo)
}
</script>

<style scoped>
.login-meeple {
  width: 84px;
  height: 84px;
  margin: 0 auto 0.75rem;
}

.login-title {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 2rem;
  font-weight: 600;
  line-height: 1;
}
</style>
