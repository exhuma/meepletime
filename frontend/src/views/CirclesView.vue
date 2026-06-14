<template>
  <v-container class="pa-4">
    <header class="mt-head">
      <div>
        <h1 class="text-h5 mt-head__title">My Circles</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Your game-night crews
        </p>
      </div>
      <MtButton
        variant="ghost"
        tone="primary"
        icon="mdi-key-variant"
        @click="joinDialog = true"
      >
        Join
      </MtButton>
    </header>

    <!-- Empty state -->
    <MtCard
      v-if="!isBusy && circlesState.circles.value.length === 0"
      class="pa-8 text-center mt-6"
    >
      <div class="mt-empty__meeple">
        <v-icon size="80" color="primary-accent">mdi-dice-multiple</v-icon>
      </div>
      <h2 class="text-h6 mb-2">No circles yet</h2>
      <p class="text-body-2 text-medium-emphasis mb-0">
        Create your first circle, or join one with an invite PIN.
      </p>
    </MtCard>

    <!-- Circle hero cards -->
    <div v-else-if="!isBusy" class="mt-tiles mt-6">
      <MtCard
        v-for="circle in circlesState.circles.value"
        :key="circle.id"
        interactive
        :to="`/circles/${circle.id}`"
        class="circle-card"
      >
        <div class="circle-card__hero" :style="heroStyle(circle)">
          <span v-if="!circle.image_ref" class="circle-card__initials">
            {{ initials(circle.name) }}
          </span>
        </div>
        <div class="circle-card__body">
          <div class="circle-card__name">{{ circle.name }}</div>
          <div class="circle-card__desc text-medium-emphasis">
            {{ circle.description || 'No description yet' }}
          </div>
          <div class="circle-card__next text-medium-emphasis">
            <v-icon size="14" start>mdi-calendar-check</v-icon>
            {{ nextLabel(circle.id) }}
          </div>
        </div>
      </MtCard>
    </div>

    <MtButton
      tone="primary"
      size="x-large"
      block
      icon="mdi-plus-circle"
      class="mt-6"
      @click="createDialog = true"
    >
      Create a Circle
    </MtButton>

    <CreateCircleDialog v-model="createDialog" @created="onCircleCreated" />

    <MtDialog v-model="joinDialog" title="Join a Circle" :max-width="400">
      <p class="text-body-2 text-medium-emphasis mb-4">
        Enter the invite PIN a host shared with you.
      </p>
      <MtPinField v-model="joinToken" @valid="joinValid = $event" />
      <template #actions>
        <v-spacer />
        <MtButton variant="ghost" tone="primary" @click="joinDialog = false">
          Cancel
        </MtButton>
        <MtButton tone="primary" :disabled="!joinValid" @click="goToJoin">
          Join
        </MtButton>
      </template>
    </MtDialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import CreateCircleDialog from '../components/CreateCircleDialog.vue'
import { useAppBar } from '../composables/appBar'
import { MtButton, MtCard, MtDialog, MtPinField } from '../ui'
import { resolveImageUrl } from '../lib/circleImage'
import type { Circle } from '../types'

// nextViableDate (from ../lib/circleStatus) and safeFormat (from
// ../lib/datetime) are intentionally not imported here: the circles-list
// endpoint does not yet return per-circle viability data, so there is
// nothing to pass to nextViableDate. When the payload includes a viability
// map, nextLabel can become:
//   const d = nextViableDate(map, todayStr)
//   return d ? 'Next: ' + safeFormat(d, 'EEE, MMM d') : 'No upcoming viable days'

const circlesState = useCircles()
const router = useRouter()

const createDialog = ref(false)
const joinDialog = ref(false)
const joinToken = ref('')
const joinValid = ref(false)
const { startJob, endJob, isBusy } = useAppBar()

function heroStyle(c: Pick<Circle, 'image_ref'>) {
  const url = resolveImageUrl(c.image_ref)
  return url
    ? { backgroundImage: `url("${url.replace(/"/g, '%22')}")` }
    : {
        background:
          'linear-gradient(135deg, rgb(var(--v-theme-primary)),' +
          ' rgb(var(--v-theme-tertiary)))',
      }
}

function initials(name: string): string {
  return name.trim().slice(0, 2).toUpperCase()
}

// TODO: when the circles-list payload includes a viability map per circle,
// replace this with nextViableDate + safeFormat (see comment above).
function nextLabel(_circleId: string): string {
  return 'Open to see upcoming days'
}

onMounted(async () => {
  startJob('loading-circles-view')
  try {
    await circlesState.fetchCircles()
  } finally {
    endJob('loading-circles-view')
  }
})

/** Close the create dialog after a circle has been created. */
function onCircleCreated(): void {
  createDialog.value = false
}

/** Navigate to the join page for the entered invite PIN. */
function goToJoin(): void {
  if (!joinValid.value) return
  joinDialog.value = false
  router.push(`/join/${joinToken.value}`)
}
</script>

<style scoped>
.mt-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.mt-head__title {
  line-height: 1.1;
}

.mt-empty__meeple {
  width: 88px;
  height: 88px;
  margin: 0 auto 1rem;
  opacity: 0.9;
}

.mt-tiles {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.circle-card__hero {
  height: 120px;
  background-size: cover;
  background-position: center;
  border-radius: var(--mt-card-radius, 12px) var(--mt-card-radius, 12px) 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Scrim darkens photo backgrounds via blend-mode; on the gradient fallback
     initials stay legible thanks to text-shadow on .circle-card__initials */
  background-color: rgba(0, 0, 0, 0.18);
  background-blend-mode: multiply;
}

.circle-card__initials {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-weight: 700;
  font-size: 2.2rem;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.04em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}

.circle-card__body {
  padding: 0.9rem 1rem;
}

.circle-card__name {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-weight: 600;
  font-size: 1.2rem;
  line-height: 1.2;
  margin-bottom: 0.25rem;
}

.circle-card__desc {
  font-size: 0.85rem;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.circle-card__next {
  font-size: 0.8rem;
  margin-top: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
</style>
