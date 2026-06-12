<template>
  <MtDialog
    :model-value="modelValue"
    title="Create a Circle"
    :max-width="500"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-alert
      v-if="error"
      type="error"
      class="mb-4"
      closable
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>
    <v-form @submit.prevent="handleCreate">
      <v-text-field
        v-model="form.name"
        label="Circle Name"
        variant="outlined"
        required
        class="mb-3"
      />
      <v-textarea
        v-model="form.description"
        label="Description (optional)"
        variant="outlined"
        rows="2"
        class="mb-3"
      />
      <v-autocomplete
        v-model="form.timezone"
        label="Timezone"
        :items="timezones"
        hint="The time-zone the events in this circle will be scheduled in."
        persistent-hint
        variant="outlined"
        class="mb-3"
      />
      <v-checkbox
        v-model="form.host_needed"
        label="This circle requires a host"
        hint="At least one member must host to make events viable."
        persistent-hint
        color="primary"
        class="mb-3"
      />
      <v-row>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model.number="form.minimum_attendees"
            label="Min attendees"
            type="number"
            variant="outlined"
            min="1"
            hint="The number of participants needed to make a session viable."
            persistent-hint
            clearable
          />
        </v-col>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model.number="form.soft_max_attendees"
            label="Soft max"
            type="number"
            variant="outlined"
            min="1"
            hint="The number of participants at which a sessions feels crowded"
            persistent-hint
            clearable
          />
        </v-col>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model.number="form.hard_max_attendees"
            label="Hard max"
            type="number"
            variant="outlined"
            min="1"
            hint="The maximum number of participants a session can support."
            persistent-hint
            clearable
          />
        </v-col>
      </v-row>
    </v-form>

    <template #actions>
      <v-spacer />
      <MtButton
        variant="ghost"
        tone="primary"
        @click="$emit('update:modelValue', false)"
      >
        Cancel
      </MtButton>
      <MtButton
        tone="primary"
        :loading="loading"
        :disabled="!form.name.trim()"
        @click="handleCreate"
      >
        Create
      </MtButton>
    </template>
  </MtDialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useCircles } from '../composables/circles'
import { ApiError } from '../api'
import { MtDialog, MtButton } from '../ui'

defineProps<{
  modelValue: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  created: []
}>()

const circles = useCircles()
const loading = ref(false)
const error = ref('')

const timezones = Intl.supportedValuesOf('timeZone')

const form = reactive({
  name: '',
  description: '',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  host_needed: false,
  minimum_attendees: null as number | null,
  soft_max_attendees: null as number | null,
  hard_max_attendees: null as number | null,
})

async function handleCreate(): Promise<void> {
  if (!form.name.trim()) return
  error.value = ''
  loading.value = true
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description || null,
      timezone: form.timezone,
      host_needed: form.host_needed,
      minimum_attendees: form.minimum_attendees || null,
      soft_max_attendees: form.soft_max_attendees || null,
      hard_max_attendees: form.hard_max_attendees || null,
    }
    await circles.createCircle(payload)
    emit('created')
    emit('update:modelValue', false)
    form.name = ''
    form.description = ''
    form.timezone = 'UTC'
    form.host_needed = false
    form.minimum_attendees = null
    form.soft_max_attendees = null
    form.hard_max_attendees = null
  } catch (e: unknown) {
    const detail =
      e instanceof ApiError
        ? (e.data as { detail?: string } | null)?.detail
        : null
    error.value = detail ?? 'Failed to create circle.'
  } finally {
    loading.value = false
  }
}
</script>
