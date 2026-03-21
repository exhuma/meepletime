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
    const returnTo =
      (user.state as string | undefined) ?? '/circles'
    await router.replace(returnTo)
  } catch (err) {
    errorMsg.value =
      'Authentication failed. Please try again.'
    console.error('OIDC callback error:', err)
  }
})
</script>
