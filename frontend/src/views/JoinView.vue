<template>
  <v-container class="fill-height pa-4" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-alert v-if="error && !isBusy" type="error" class="mb-4">{{
          error
        }}</v-alert>

        <v-card v-if="!isBusy && circleInfo" class="pa-4" elevation="4">
          <v-card-title class="text-h6 mb-1">Join Circle</v-card-title>
          <v-card-subtitle class="mb-4">{{ circleInfo.name }}</v-card-subtitle>
          <v-card-text>
            <p v-if="circleInfo.description" class="text-body-2 mb-4">
              {{ circleInfo.description }}
            </p>
            <v-form @submit.prevent="handleJoin">
              <v-text-field
                v-model="pseudonym"
                label="Your display name"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                required
                class="mb-3"
              />
              <v-checkbox
                v-model="canHostDefault"
                label="I can host"
                color="primary"
                hide-details
                class="mb-4"
              />
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="joining"
                :disabled="!pseudonym.trim()"
              >
                Join Circle
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import api, { ApiError } from '../api'
import type { Circle } from '../types'
import { useAppBar } from '../composables/appBar'

const route = useRoute()
const router = useRouter()
const circles = useCircles()

const token = route.params.token as string
const joining = ref(false)
const error = ref('')
const circleInfo = ref<Circle | null>(null)
const pseudonym = ref('')
const canHostDefault = ref(false)
const { startJob, endJob, isBusy } = useAppBar()

onMounted(async () => {
  startJob('loading-join-view')
  try {
    circleInfo.value = await api.get<Circle>(`/circles/join/${token}`)
  } catch {
    error.value = 'Invalid or expired invite token.'
  } finally {
    endJob('loading-join-view')
  }
})

async function handleJoin(): Promise<void> {
  joining.value = true
  try {
    await circles.joinCircle(
      token,
      pseudonym.value.trim(),
      canHostDefault.value,
    )
    router.push('/circles')
  } catch (e: unknown) {
    const detail =
      e instanceof ApiError
        ? (e.data as { detail?: string } | null)?.detail
        : null
    error.value = detail ?? 'Failed to join circle.'
  } finally {
    joining.value = false
  }
}
</script>
