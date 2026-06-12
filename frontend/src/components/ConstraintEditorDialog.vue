<template>
  <MtDialog
    v-model="isOpen"
    :title="`My constraints — ${formattedDate}`"
    :max-width="480"
  >
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      class="mb-3"
    />
    <v-text-field
      v-model="form.min"
      label="Minimum attendees"
      type="number"
      :placeholder="
        props.circle.minimum_attendees !== null
          ? String(props.circle.minimum_attendees)
          : 'Circle default'
      "
      clearable
      density="compact"
      variant="outlined"
      class="mb-3"
      hide-details="auto"
      min="0"
    />
    <v-text-field
      v-model="form.soft"
      label="Soft max attendees"
      type="number"
      :placeholder="
        props.circle.soft_max_attendees !== null
          ? String(props.circle.soft_max_attendees)
          : 'Circle default'
      "
      clearable
      density="compact"
      variant="outlined"
      class="mb-3"
      hide-details="auto"
      min="0"
    />
    <v-text-field
      v-model="form.hard"
      label="Hard max attendees"
      type="number"
      :placeholder="
        props.circle.hard_max_attendees !== null
          ? String(props.circle.hard_max_attendees)
          : 'Circle default'
      "
      clearable
      density="compact"
      variant="outlined"
      hide-details="auto"
      min="0"
    />

    <template #actions>
      <MtButton
        v-if="existing"
        variant="ghost"
        tone="danger"
        :loading="saving"
        @click="clearConstraint"
      >
        Clear
      </MtButton>
      <v-spacer />
      <MtButton
        variant="ghost"
        tone="primary"
        :disabled="saving"
        @click="close"
      >
        Cancel
      </MtButton>
      <MtButton tone="primary" :loading="saving" @click="save">Save</MtButton>
    </template>
  </MtDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { safeFormat } from '../lib/datetime'
import { useCircles } from '../composables/circles'
import { MtDialog, MtButton } from '../ui'
import type { Circle, HostDayConstraint } from '../types'

const props = defineProps<{
  modelValue: boolean
  circleId: string
  /** ISO date string (YYYY-MM-DD) for the constrained day. */
  date: string
  /** Circle record used to display default values as placeholders. */
  circle: Circle
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved'): void
  (e: 'deleted'): void
}>()

const circlesState = useCircles()
const loading = ref(false)
const saving = ref(false)
const existing = ref<HostDayConstraint | null>(null)
const form = ref<{
  min: string | null
  soft: string | null
  hard: string | null
}>({ min: null, soft: null, hard: null })

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const formattedDate = computed<string>(() =>
  safeFormat(props.date, 'EEEE, MMMM d, yyyy'),
)

/** Convert a form string value to number | null for the API payload. */
function parseOptInt(v: string | null): number | null {
  if (v === null || v === '') return null
  const n = parseInt(v, 10)
  return Number.isNaN(n) ? null : n
}

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    loading.value = true
    try {
      existing.value = await circlesState.fetchMyConstraint(
        props.circleId,
        props.date,
      )
      if (existing.value) {
        const c = existing.value
        form.value = {
          min:
            c.override_minimum_attendees !== null
              ? String(c.override_minimum_attendees)
              : null,
          soft:
            c.override_soft_max_attendees !== null
              ? String(c.override_soft_max_attendees)
              : null,
          hard:
            c.override_hard_max_attendees !== null
              ? String(c.override_hard_max_attendees)
              : null,
        }
      } else {
        form.value = { min: null, soft: null, hard: null }
      }
    } finally {
      loading.value = false
    }
  },
)

async function save(): Promise<void> {
  saving.value = true
  try {
    await circlesState.setMyConstraint(props.circleId, props.date, {
      override_minimum_attendees: parseOptInt(form.value.min),
      override_soft_max_attendees: parseOptInt(form.value.soft),
      override_hard_max_attendees: parseOptInt(form.value.hard),
    })
    emit('saved')
    close()
  } finally {
    saving.value = false
  }
}

async function clearConstraint(): Promise<void> {
  saving.value = true
  try {
    await circlesState.deleteMyConstraint(props.circleId, props.date)
    emit('deleted')
    close()
  } finally {
    saving.value = false
  }
}

function close(): void {
  emit('update:modelValue', false)
}
</script>
