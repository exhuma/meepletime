<template>
  <v-dialog
    :model-value="modelValue"
    :max-width="maxWidth"
    v-bind="$attrs"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <MtCard class="mt-dialog">
      <header v-if="title || $slots.title" class="mt-dialog__title">
        <slot name="title">{{ title }}</slot>
      </header>
      <div class="mt-dialog__body"><slot /></div>
      <footer v-if="$slots.actions" class="mt-dialog__actions">
        <slot name="actions" />
      </footer>
    </MtCard>
  </v-dialog>
</template>

<script setup lang="ts">
import MtCard from './MtCard.vue'

defineOptions({ inheritAttrs: false })

/**
 * Standard dialog frame: a `v-dialog` wrapping an MtCard with
 * title / body / actions slots, so the ~20 dialogs stop repeating the
 * same scaffold. `v-bind="$attrs"` passes through any v-dialog prop.
 */
withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    maxWidth?: number | string
  }>(),
  { maxWidth: 480 },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>

<style scoped>
.mt-dialog__title {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 1.3rem;
  font-weight: 600;
  padding: 1.25rem 1.25rem 0.25rem;
}

.mt-dialog__body {
  padding: 0.75rem 1.25rem;
}

.mt-dialog__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem 1.25rem;
}
</style>
