<template>
  <div class="d-flex flex-column align-center">
    <div
      class="invite-pin__code"
      role="text"
      :aria-label="`Invite PIN ${[...pin].join(' ')}`"
    >
      {{ pin }}
    </div>
    <MtButton
      variant="soft"
      tone="primary"
      size="small"
      class="mt-3"
      :icon="copied ? 'mdi-check' : 'mdi-content-copy'"
      @click="copy"
    >
      {{ copied ? 'Copied' : 'Copy PIN' }}
    </MtButton>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MtButton } from '../ui'

const props = defineProps<{ pin: string }>()

const copied = ref(false)

/** Copy the bare PIN to the clipboard with transient feedback. */
async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.pin)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    // clipboard API not available
  }
}
</script>

<style scoped>
.invite-pin__code {
  font-family: var(--v-font-family-display, sans-serif);
  font-size: 2.1rem;
  font-weight: 700;
  /* Trailing letter-spacing is offset by padding-left to keep the
     code visually centered. */
  letter-spacing: 0.32em;
  padding: 0.5rem 0.7rem 0.5rem 1rem;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  border: 2px dashed rgba(var(--v-theme-primary), 0.5);
  border-radius: var(--mt-field-radius);
  line-height: 1.2;
}
</style>
