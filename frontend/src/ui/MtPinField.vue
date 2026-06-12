<template>
  <v-text-field
    :model-value="modelValue"
    :label="label"
    placeholder="ABC234"
    prepend-inner-icon="mdi-key-variant"
    :maxlength="INVITE_LENGTH"
    hint="6 characters, e.g. ABC234"
    persistent-hint
    class="mt-pin"
    v-bind="$attrs"
    @update:model-value="onInput"
  />
</template>

<script setup lang="ts">
import { normalizePin, isValidPin, INVITE_LENGTH } from '../lib/invite'

defineOptions({ inheritAttrs: false })

/**
 * Invite-PIN input. Encapsulates canonicalisation (uppercase, drop
 * ambiguous characters, cap length) and the monospaced "stamp" styling
 * that used to be duplicated across views. `v-model` is the canonical
 * PIN; `valid` reports completeness.
 */
withDefaults(
  defineProps<{
    modelValue: string
    label?: string
  }>(),
  { label: 'Invite PIN' },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'valid', value: boolean): void
}>()

/** Canonicalise on every keystroke and report validity. */
function onInput(raw: string): void {
  const pin = normalizePin(raw)
  emit('update:modelValue', pin)
  emit('valid', isValidPin(pin))
}
</script>

<style scoped>
.mt-pin :deep(input) {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-family: var(--v-font-family-display, sans-serif);
  font-weight: 700;
  font-size: 1.15rem;
}
</style>
