<template>
  <MtDialog
    :model-value="modelValue"
    :max-width="480"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #title>
      <span class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-qrcode</v-icon>
        Invite to {{ circle.name }}
      </span>
    </template>

    <p class="text-caption text-medium-emphasis text-center mb-1">
      Enter this PIN to join:
    </p>
    <div class="mb-4">
      <InvitePinDisplay :pin="circle.invite_token" />
    </div>

    <p class="text-body-2 mb-1 font-weight-medium">Or scan / share:</p>
    <div class="d-flex align-center mb-4">
      <v-text-field
        :model-value="inviteUrl"
        readonly
        variant="outlined"
        density="compact"
        hide-details
        class="flex-grow-1 mr-2"
      />
      <MtButton
        variant="icon"
        tone="primary"
        :icon="copied ? 'mdi-check' : 'mdi-content-copy'"
        title="Copy link"
        @click="copyLink"
      />
    </div>

    <div class="d-flex justify-center mb-4">
      <img
        v-if="qrDataUrl"
        :src="qrDataUrl"
        alt="QR Code for invite link"
        width="200"
        height="200"
        class="invite-qr"
      />
      <v-progress-circular v-else indeterminate color="primary" />
    </div>

    <v-alert
      v-if="regenerateError"
      type="error"
      class="mb-1"
      closable
      @click:close="regenerateError = ''"
    >
      {{ regenerateError }}
    </v-alert>

    <template #actions>
      <MtButton
        v-if="isAdmin"
        variant="soft"
        tone="primary"
        icon="mdi-refresh"
        :loading="regenerating"
        @click="regenerate"
      >
        Regenerate PIN
      </MtButton>
      <v-spacer />
      <MtButton
        variant="ghost"
        tone="primary"
        @click="$emit('update:modelValue', false)"
      >
        Close
      </MtButton>
    </template>
  </MtDialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import QRCode from 'qrcode'
import { useCircles } from '../composables/circles'
import InvitePinDisplay from './InvitePinDisplay.vue'
import { MtDialog, MtButton } from '../ui'
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

<style scoped>
/* The QR image already carries its own white quiet zone; just round it. */
.invite-qr {
  border-radius: var(--mt-field-radius);
}
</style>
