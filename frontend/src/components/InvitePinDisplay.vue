<template>
  <div class="d-flex flex-column align-center">
    <div
      class="invite-pin__code"
      role="text"
      :aria-label="`Invite PIN ${[...pin].join(' ')}`"
    >
      {{ pin }}
    </div>
    <v-btn
      variant="tonal"
      color="primary"
      size="small"
      class="mt-2"
      @click="copy"
    >
      <v-icon start>{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
      {{ copied ? 'Copied' : 'Copy PIN' }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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
  font-size: 2.25rem;
  font-weight: 700;
  /* Trailing letter-spacing is offset by padding-left to keep the
     code visually centered. */
  letter-spacing: 0.3em;
  padding-left: 0.3em;
  color: rgb(var(--v-theme-primary));
  line-height: 1.2;
}
</style>
