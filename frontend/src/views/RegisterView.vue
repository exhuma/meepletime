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
import { useAuth } from '../composables/auth'

const auth = useAuth()

onMounted(async () => {
  await auth.login('/')
})
</script>
