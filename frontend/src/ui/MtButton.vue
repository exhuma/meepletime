<template>
  <v-btn
    :class="['mt-btn', `mt-btn--${variant}`]"
    :color="vColor"
    :variant="vVariant"
    :block="block"
    :size="size"
    :loading="loading"
    :rounded="variant === 'icon' ? 'circle' : 'lg'"
    :icon="variant === 'icon' ? true : undefined"
    :prepend-icon="variant !== 'icon' ? icon : undefined"
    v-bind="$attrs"
  >
    <v-icon v-if="variant === 'icon'">{{ icon }}</v-icon>
    <slot v-else />
  </v-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

/**
 * Chunky, tactile button — a wooden game token you press onto the
 * board. A thin façade over `v-btn`: unmapped props pass straight
 * through via `$attrs`, so the escape hatch to raw Vuetify stays open.
 */
const props = withDefaults(
  defineProps<{
    /** solid (filled token) | soft (tonal) | ghost (text) | icon. */
    variant?: 'solid' | 'soft' | 'ghost' | 'icon'
    /** Semantic colour role. */
    tone?: 'primary' | 'host' | 'attend' | 'danger'
    block?: boolean
    size?: string
    loading?: boolean
    /** Leading icon (or the glyph itself when variant="icon"). */
    icon?: string
  }>(),
  { variant: 'solid', tone: 'primary' },
)

const vColor = computed(() => {
  if (props.tone === 'danger') return 'error'
  // Icon/ghost buttons read as light accents on dark surfaces.
  if (
    props.tone === 'primary' &&
    (props.variant === 'icon' || props.variant === 'ghost')
  ) {
    return 'primary-accent'
  }
  return props.tone
})

const vVariant = computed(() => {
  switch (props.variant) {
    case 'soft':
      return 'tonal'
    case 'ghost':
    case 'icon':
      return 'text'
    default:
      return 'flat'
  }
})
</script>

<style scoped>
/* The "token" treatment: a solid base lip that compresses on press. */
.mt-btn--solid {
  box-shadow:
    0 var(--mt-token-lip) 0 0 var(--mt-token-edge),
    var(--mt-shadow-card);
  transition:
    transform var(--mt-press-ms) ease,
    box-shadow var(--mt-press-ms) ease;
}

.mt-btn--solid:active {
  transform: translateY(var(--mt-token-lip));
  box-shadow: 0 0 0 0 var(--mt-token-edge);
}

.mt-btn--soft:active,
.mt-btn--ghost:active,
.mt-btn--icon:active {
  transform: scale(0.94);
}
</style>
