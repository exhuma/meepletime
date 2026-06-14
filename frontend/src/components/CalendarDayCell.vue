<template>
  <div
    class="cell"
    :class="{
      'cell--past': vs.isPast,
      'cell--viable': vs.fill === 'viable',
      'cell--over-soft-max': vs.fill === 'over-soft-max',
      'cell--dimmed': vs.isDimmed,
      'cell--hosting': myState === 'hosting',
    }"
    role="button"
    :tabindex="dimmed ? -1 : 0"
    :aria-label="ariaLabel"
    @pointerdown="lp.onPointerdown"
    @pointermove="lp.onPointermove"
    @pointerup="lp.onPointerup"
    @pointercancel="lp.onPointercancel"
    @contextmenu="lp.onContextmenu"
    @click="lp.onClick"
    @keydown.enter.prevent="emit('activate', date)"
    @keydown.space.prevent="emit('activate', date)"
    @keydown.f10.shift.prevent="emit('context', date)"
  >
    <span
      v-if="vs.multipleHostsWarning"
      class="cell__warn"
      aria-hidden="true"
    />
    <span class="cell__date" :class="{ 'cell__date--today': isToday }">
      {{ dayOfMonth }}
    </span>
    <span v-if="myState === 'hosting'" class="cell__mine">
      <v-icon size="15" color="host">mdi-home-variant</v-icon>
    </span>
    <span v-else-if="myState === 'attending'" class="cell__mine">
      <v-icon size="15" color="attend">mdi-check-circle</v-icon>
    </span>
    <span v-if="vs.attendeeCount !== null" class="cell__count">
      {{ vs.attendeeCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DayViability } from '../types'
import { useLongPress } from '../composables/useLongPress'
import { dayVisualState } from '../lib/viability'

const props = defineProps<{
  date: string
  dayOfMonth: number
  myState: 'attending' | 'hosting' | null
  viability: DayViability | null
  isToday: boolean
  isPast: boolean
  dimmed: boolean
}>()

const emit = defineEmits<{
  activate: [date: string]
  context: [date: string]
}>()

const lp = useLongPress({
  onTap: () => emit('activate', props.date),
  onLongPress: () => emit('context', props.date),
})

/** Semantic visual state derived from this day's viability. */
const vs = computed(() =>
  dayVisualState(props.viability, {
    isPast: props.isPast,
    dimmed: props.dimmed,
  }),
)

/** Screen-reader description of the cell's date and state. */
const ariaLabel = computed<string>(() => {
  const parts = [`Day ${props.dayOfMonth}`]
  if (props.isToday) parts.push('today')
  if (props.myState === 'hosting') parts.push('you are hosting')
  else if (props.myState === 'attending') parts.push('you are attending')
  if (props.viability?.is_viable) parts.push('viable')
  return parts.join(', ')
})
</script>

<style scoped>
.cell {
  background: rgb(var(--v-theme-surface));
  min-height: clamp(52px, 13vw, 76px);
  padding: 4px 5px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  cursor: pointer;
  user-select: none;
  border-radius: 0.6rem;
  /* Allow vertical page scroll; long-press is cancelled on move. */
  touch-action: pan-y;
  transition:
    background 0.12s ease,
    transform 0.08s ease;
}

.cell:hover {
  background: rgb(var(--v-theme-surface-container));
}

.cell:active {
  transform: scale(0.97);
}

.cell:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -2px;
}

.cell--past {
  background: rgb(var(--v-theme-surface-container-lowest));
  opacity: 0.55;
}

.cell--viable {
  background: rgb(var(--v-theme-viable-container));
}

.cell--over-soft-max {
  background: rgb(var(--v-theme-tertiary-container));
}

.cell--dimmed {
  opacity: 0.25;
  pointer-events: none;
}

.cell__date {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.4;
  min-width: 1.6em;
  text-align: center;
}

.cell__date--today {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-radius: 999px;
}

.cell--hosting {
  box-shadow: inset 0 0 0 2px rgb(var(--v-theme-host));
}

.cell__mine {
  margin-top: 2px;
}

.cell__count {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface-variant));
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 4px;
  padding: 1px 4px;
}

.cell__warn {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgb(var(--v-theme-tertiary));
}
</style>
