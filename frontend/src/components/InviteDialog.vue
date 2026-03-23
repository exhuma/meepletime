<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="480"
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-qrcode</v-icon>
        Invite to {{ circle.name }}
      </v-card-title>
      <v-divider />
      <v-card-text class="pt-4">
        <p class="text-body-2 mb-1 font-weight-medium">Invite link:</p>
        <div class="d-flex align-center mb-4">
          <v-text-field
            :model-value="inviteUrl"
            readonly
            variant="outlined"
            density="compact"
            hide-details
            class="flex-grow-1 mr-2"
          />
          <v-btn icon variant="text" @click="copyLink" :title="'Copy link'">
            <v-icon>{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
          </v-btn>
        </div>

        <div class="d-flex justify-center mb-4">
          <img
            v-if="qrDataUrl"
            :src="qrDataUrl"
            alt="QR Code for invite link"
            width="200"
            height="200"
          />
          <v-progress-circular v-else indeterminate color="primary" />
        </div>

        <p class="text-caption text-medium-emphasis text-center mb-2">
          Scan or share the link. Token: <code>{{ circle.invite_token }}</code>
        </p>

        <v-alert
          v-if="regenerateError"
          type="error"
          class="mb-3"
          closable
          @click:close="regenerateError = ''"
        >
          {{ regenerateError }}
        </v-alert>
      </v-card-text>
      <v-divider />
      <v-card-actions class="pa-3">
        <v-btn
          v-if="isAdmin"
          color="tertiary"
          variant="tonal"
          :loading="regenerating"
          @click="regenerate"
        >
          <v-icon start>mdi-refresh</v-icon>Regenerate Token
        </v-btn>
        <v-spacer />
        <v-btn @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import QRCode from 'qrcode'
import { useCircles } from '../composables/circles'
import type { Circle } from '../types'

const props = defineProps<{
  modelValue: boolean
  circle: Circle
  isAdmin: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  regenerated: []
}>()

const circlesState = useCircles()

const qrDataUrl = ref<string | null>(null)
const copied = ref(false)
const regenerating = ref(false)
const regenerateError = ref('')

/** The full invite URL built from window.location origin and the circle's invite token. */
const inviteUrl = computed<string>(
  () => `${window.location.origin}/join/${props.circle.invite_token}`,
)

/** Generate the QR code data URL whenever the invite URL changes. */
async function generateQr(): Promise<void> {
  try {
    qrDataUrl.value = await QRCode.toDataURL(inviteUrl.value, { width: 200 })
  } catch {
    qrDataUrl.value = null
  }
}

/** Copy the invite link to the clipboard. */
async function copyLink(): Promise<void> {
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    // clipboard API not available
  }
}

/** Regenerate the circle's invite token (owner/admin only). */
async function regenerate(): Promise<void> {
  regenerating.value = true
  regenerateError.value = ''
  try {
    await circlesState.regenerateInvite(props.circle.id)
    emit('regenerated')
  } catch {
    regenerateError.value = 'Failed to regenerate token.'
  } finally {
    regenerating.value = false
  }
}

watch(
  () => [props.modelValue, inviteUrl.value] as const,
  ([isOpen]) => {
    if (isOpen) generateQr()
  },
  { immediate: true },
)
</script>
