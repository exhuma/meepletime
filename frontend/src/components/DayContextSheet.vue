<template>
  <v-bottom-sheet v-model="isOpen" max-width="600">
    <v-card>
      <v-card-title class="text-subtitle-1 pt-4 px-4">
        {{ formattedDate }}
      </v-card-title>

      <v-list>
        <v-list-item
          prepend-icon="mdi-calendar-search"
          title="View day details"
          @click="onViewDetails"
        />
        <v-list-item
          v-if="presenceState === 'hosting' && !isPast"
          prepend-icon="mdi-tune"
          title="Edit my constraints for this day"
          @click="onEditConstraints"
        />
      </v-list>

      <v-card-actions class="pb-4 px-4">
        <v-spacer />
        <v-btn variant="text" @click="close">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { safeFormat } from '../lib/datetime'

const props = defineProps<{
  modelValue: boolean
  /** ISO date string (YYYY-MM-DD) for the selected day. */
  date: string
  /** True when the selected day is in the past. */
  isPast: boolean
  /** The current user's presence state for the selected day. */
  presenceState: 'attending' | 'hosting' | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'view-details'): void
  (e: 'edit-constraints'): void
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const formattedDate = computed<string>(() =>
  safeFormat(props.date, 'EEEE, MMMM d, yyyy'),
)

function close(): void {
  emit('update:modelValue', false)
}

function onViewDetails(): void {
  emit('view-details')
  close()
}

function onEditConstraints(): void {
  emit('edit-constraints')
  close()
}
</script>
