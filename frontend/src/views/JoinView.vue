<template>
  <v-container class="fill-height pa-4" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-alert v-if="error && !isBusy" type="error" class="mb-4">{{
          error
        }}</v-alert>

        <MtCard v-if="!isBusy && circleInfo" tone="primary" class="pa-5">
          <div class="join-head">
            <div class="join-meeple">
              <v-icon size="48" color="primary-accent"
                >mdi-dice-multiple</v-icon
              >
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">
                You're invited to
              </div>
              <h1 class="join-title">{{ circleInfo.name }}</h1>
            </div>
          </div>
          <p
            v-if="circleInfo.description"
            class="text-body-2 text-medium-emphasis my-4"
          >
            {{ circleInfo.description }}
          </p>
          <v-form class="mt-4" @submit.prevent="handleJoin">
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
            <MtButton
              type="submit"
              tone="primary"
              size="large"
              block
              :loading="joining"
              :disabled="!pseudonym.trim()"
            >
              Join Circle
            </MtButton>
          </v-form>
        </MtCard>
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
import { normalizePin } from '../lib/invite'
import { MtCard, MtButton } from '../ui'

const route = useRoute()
const router = useRouter()
const circles = useCircles()

const token = normalizePin(route.params.token as string)
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
    error.value = 'Invalid or expired invite PIN.'
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

<style scoped>
.join-head {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.join-meeple {
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
}

.join-title {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.1;
}
</style>
