<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" class="text-center">
        <v-progress-circular
          v-if="!errorMsg"
          indeterminate
          color="primary"
          size="48"
        />
        <v-alert
          v-else
          type="error"
          class="mt-4"
        >
          {{ errorMsg }}
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { userManager } from '../auth/oidc'

const router = useRouter()
const errorMsg = ref<string | null>(null)

onMounted(async () => {
  try {
    const user = await userManager.signinRedirectCallback()
    const raw = (user.state as string | undefined) ?? ''
    // Reject auth-flow paths as returnTo targets to prevent
    // edge-case loops caused by corrupted PKCE state.
    const unsafe =
      raw === '/login' ||
      raw.startsWith('/auth/callback') ||
      raw === ''
    const returnTo = unsafe ? '/circles' : raw
    await router.replace(returnTo)
  } catch (err) {
    console.error('OIDC callback error:', err)
    // "No matching state" means the PKCE state was lost
    // (e.g. origin mismatch, stale tab). Restarting the
    // login flow recovers automatically.
    if (
      err instanceof Error &&
      err.message.includes('No matching state')
    ) {
      await router.replace('/login')
      return
    }
    errorMsg.value =
      'Authentication failed. Please try again.'
  }
})
</script>
