<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" class="text-center">
        <v-progress-circular indeterminate color="primary" size="48" />
        <p class="mt-4 text-medium-emphasis">Redirecting to sign in…</p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'
import { userManager } from '../auth/oidc'

const auth = useAuth()
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const returnTo = (route.query.returnTo as string) ?? '/'
  // Skip the OIDC redirect if the user already has a valid
  // session — navigating to /login while authenticated should
  // just take them to their destination immediately.
  const existing = await userManager.getUser()
  if (existing && !existing.expired) {
    await router.replace(returnTo)
    return
  }
  await auth.login(returnTo)
})
</script>
