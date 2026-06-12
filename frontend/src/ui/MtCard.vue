<template>
  <v-card
    :class="['mt-card', { 'mt-card--interactive': interactive }]"
    :style="toneStyle"
    v-bind="$attrs"
  >
    <slot />
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

/**
 * A board-tile surface. Thin wrapper over `v-card`: an optional tone
 * accent stripe and an interactive (hover-lift / press) affordance.
 * Pass `to`, `href`, etc. straight through via `$attrs`.
 */
const props = withDefaults(
  defineProps<{
    /** Accent colour for the top stripe (none when omitted). */
    tone?: 'primary' | 'host' | 'attend' | 'viable'
    /** Adds hover-lift and press feedback (use for clickable tiles). */
    interactive?: boolean
  }>(),
  {},
)

const toneStyle = computed(() =>
  props.tone ? { '--mt-card-accent': `rgb(var(--v-theme-${props.tone}))` } : {},
)
</script>

<style scoped>
.mt-card {
  position: relative;
  overflow: hidden;
}

/* Tone accent: a colourful rail along the top edge of the tile. */
.mt-card[style*='--mt-card-accent']::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 0.32rem;
  background: var(--mt-card-accent);
}

.mt-card--interactive {
  cursor: pointer;
  transition:
    transform var(--mt-press-ms) ease,
    box-shadow var(--mt-press-ms) ease;
}

.mt-card--interactive:hover {
  transform: translateY(-0.18rem);
  box-shadow: var(--mt-shadow-raised) !important;
}

.mt-card--interactive:active {
  transform: translateY(0);
  box-shadow: var(--mt-shadow-card) !important;
}
</style>
