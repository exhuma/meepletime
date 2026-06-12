<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" class="text-center">
        <template v-if="!authError">
          <v-progress-circular indeterminate color="primary" size="48" />
          <p class="mt-4 text-medium-emphasis">Redirecting to sign in…</p>
        </template>
        <template v-else>
          <v-alert type="error" class="mb-4 text-left">
            Sign-in could not be completed. The server rejected the session —
            this usually happens after the identity provider was restarted.
          </v-alert>
          <v-btn color="primary" size="large" @click="retrySignIn">
            Sign in again
          </v-btn>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'
import { userManager } from '../auth/oidc'
import { clearReauthGuard, hasAuthError } from '../auth/reauthGuard'

const auth = useAuth()
const route = useRoute()
const router = useRouter()

const returnTo = (route.query.returnTo as string) ?? '/'
const authError = ref(false)

onMounted(async () => {
  // After repeated 401s on freshly issued tokens the loop breaker lands
  // us here; do not auto-redirect (that is what would loop). Offer a
  // manual retry instead.
  if (hasAuthError()) {
    authError.value = true
    return
  }
  // Skip the OIDC redirect if the user already has a valid session —
  // navigating to /login while authenticated should just take them to
  // their destination immediately.
  const existing = await userManager.getUser()
  if (existing && !existing.expired) {
    await router.replace(returnTo)
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
