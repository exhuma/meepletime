<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationSettings } from '../composables/useNotificationSettings'

const route = useRoute()
const { confirmNotificationEmail } = useNotificationSettings()

type Phase = 'working' | 'confirmed' | 'expired' | 'invalid' | 'error'
const phase = ref<Phase>('working')
const email = ref<string | null>(null)

onMounted(async () => {
  const code = route.query.code
  if (typeof code !== 'string' || !code) {
    phase.value = 'invalid'
    return
  }
  try {
    const result = await confirmNotificationEmail(code)
    phase.value = result.status
    email.value = result.email
  } catch {
    phase.value = 'error'
  }
})
</script>

<template>
  <v-container class="confirm-email" max-width="520">
    <v-card class="pa-6 text-center">
      <template v-if="phase === 'working'">
        <v-progress-circular indeterminate color="primary" />
        <p class="mt-4">Confirming your email…</p>
      </template>
      <template v-else-if="phase === 'confirmed'">
        <h1 class="text-h6 mb-2">Email confirmed</h1>
        <p>{{ email }} will now receive your MeepleTime notifications.</p>
      </template>
      <template v-else-if="phase === 'expired'">
        <h1 class="text-h6 mb-2">Link expired</h1>
        <p>
          This confirmation link is no longer valid. Request a new one from your
          profile settings.
        </p>
      </template>
      <template v-else-if="phase === 'invalid'">
        <h1 class="text-h6 mb-2">Invalid link</h1>
        <p>This confirmation link is not recognised.</p>
      </template>
      <template v-else>
        <h1 class="text-h6 mb-2">Something went wrong</h1>
        <p>Please try again in a moment.</p>
      </template>
      <v-btn class="mt-6" color="primary" to="/profile"> Go to settings </v-btn>
    </v-card>
  </v-container>
</template>

<style scoped>
.confirm-email {
  margin-top: 48px;
}
</style>
