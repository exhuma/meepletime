<template>
  <MtDialog
    :model-value="modelValue"
    title="Edit Circle"
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
    <v-alert v-if="!isAdmin" type="info" variant="tonal" class="mb-4">
      Only an owner or admin can change circle settings.
    </v-alert>
    <v-form @submit.prevent="handleSave">
      <CircleFormFields :form="form" />
      <CircleImageField
        v-model:file="imageFile"
        v-model:remove="removeImage"
        :current-image-ref="circle.image_ref"
      />
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
        :disabled="!isAdmin || !form.name.trim()"
        @click="handleSave"
      >
        Save
      </MtButton>
    </template>
  </MtDialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useCircles } from '../composables/circles'
import { ApiError } from '../api'
import { MtDialog, MtButton } from '../ui'
import CircleFormFields from './CircleFormFields.vue'
import type { CircleFormModel } from './CircleFormFields.vue'
import CircleImageField from './CircleImageField.vue'
import type { Circle } from '../types'

const props = defineProps<{
  modelValue: boolean
  circle: Circle
  isAdmin: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const circles = useCircles()
const loading = ref(false)
const error = ref('')
const imageFile = ref<File | null>(null)
const removeImage = ref(false)

const form = reactive<CircleFormModel>({
  name: '',
  description: '',
  timezone: 'UTC',
  host_needed: false,
  minimum_attendees: null,
  soft_max_attendees: null,
  hard_max_attendees: null,
})

/** Reset the form to mirror the circle each time the dialog opens. */
function syncFromCircle(): void {
  form.name = props.circle.name
  form.description = props.circle.description ?? ''
  form.timezone = props.circle.timezone
  form.host_needed = props.circle.host_needed
  form.minimum_attendees = props.circle.minimum_attendees
  form.soft_max_attendees = props.circle.soft_max_attendees
  form.hard_max_attendees = props.circle.hard_max_attendees
  imageFile.value = null
  removeImage.value = false
  error.value = ''
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) syncFromCircle()
  },
  { immediate: true },
)

async function handleSave(): Promise<void> {
  if (!props.isAdmin || !form.name.trim()) return
  error.value = ''
  loading.value = true
  try {
    await circles.updateCircle(props.circle.id, {
      name: form.name.trim(),
      description: form.description || null,
      timezone: form.timezone,
      host_needed: form.host_needed,
      minimum_attendees: form.minimum_attendees || null,
      soft_max_attendees: form.soft_max_attendees || null,
      hard_max_attendees: form.hard_max_attendees || null,
    })
    // Image is stored separately; a new file wins over a remove.
    if (imageFile.value) {
      await circles.uploadCircleImage(props.circle.id, imageFile.value)
    } else if (removeImage.value) {
      await circles.deleteCircleImage(props.circle.id)
    }
    emit('saved')
    emit('update:modelValue', false)
  } catch (e: unknown) {
    const detail =
      e instanceof ApiError
        ? (e.data as { detail?: string } | null)?.detail
        : null
    error.value = detail ?? 'Failed to save circle.'
  } finally {
    loading.value = false
  }
}
</script>
