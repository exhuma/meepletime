<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500">
    <v-card>
      <v-card-title class="text-h6 pa-4">Create a Circle</v-card-title>
      <v-divider />
      <v-card-text class="pt-4">
        <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
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
          <v-select
            v-model="form.timezone"
            label="Timezone"
            :items="timezones"
            variant="outlined"
            class="mb-3"
          />
          <v-checkbox
            v-model="form.host_needed"
            label="Host required for viable day"
            color="primary"
            hide-details
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
                clearable
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-divider />
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">Cancel</v-btn>
        <v-btn
          color="primary"
          @click="handleCreate"
          :loading="loading"
          :disabled="!form.name.trim()"
        >
          Create
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useCircles } from '../composables/circles'

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

const timezones = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Toronto',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Amsterdam',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Australia/Sydney',
  'Pacific/Auckland',
  'UTC',
]

const form = reactive({
  name: '',
  description: '',
  timezone: 'UTC',
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
    const err = e as { response?: { data?: { detail?: string } } }
    error.value = err.response?.data?.detail || 'Failed to create circle.'
  } finally {
    loading.value = false
  }
}
</script>
