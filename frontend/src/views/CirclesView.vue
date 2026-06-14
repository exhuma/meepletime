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

    <!-- Circle tiles -->
    <div v-else-if="!isBusy" class="mt-tiles mt-6">
      <MtCard
        v-for="(circle, i) in circlesState.circles.value"
        :key="circle.id"
        interactive
        :tone="toneFor(i)"
        :to="`/circles/${circle.id}`"
        class="mt-tile"
      >
        <div class="mt-tile__body">
          <div
            class="mt-tile__avatar"
            :class="`mt-tile__avatar--${toneFor(i)}`"
          >
            <v-icon size="34">mdi-dice-multiple</v-icon>
          </div>
          <div class="mt-tile__text">
            <div class="mt-tile__name">{{ circle.name }}</div>
            <div class="mt-tile__desc text-medium-emphasis">
              {{ circle.description || 'No description yet' }}
            </div>
          </div>
          <v-icon class="mt-tile__chev">mdi-chevron-right</v-icon>
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

const circlesState = useCircles()
const router = useRouter()

const createDialog = ref(false)
const joinDialog = ref(false)
const joinToken = ref('')
const joinValid = ref(false)
const { startJob, endJob, isBusy } = useAppBar()

/** Rotate meeple colours across the list for playful variety. */
const tones = ['primary', 'host', 'attend', 'viable'] as const
function toneFor(i: number): (typeof tones)[number] {
  return tones[i % tones.length]
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

.mt-tile__body {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
}

.mt-tile__avatar {
  flex: 0 0 auto;
  width: 52px;
  height: 52px;
  padding: 9px;
  border-radius: 1rem;
  box-shadow: inset 0 -3px 0 0 rgba(0, 0, 0, 0.16);
}

.mt-tile__avatar--primary {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
}

.mt-tile__avatar--host {
  background: rgb(var(--v-theme-host));
  color: rgb(var(--v-theme-on-host));
}

.mt-tile__avatar--attend {
  background: rgb(var(--v-theme-attend));
  color: rgb(var(--v-theme-on-attend));
}

.mt-tile__avatar--viable {
  background: rgb(var(--v-theme-viable));
  color: rgb(var(--v-theme-on-viable));
}

.mt-tile__text {
  min-width: 0;
  flex: 1 1 auto;
}

.mt-tile__name {
  font-family: var(--v-font-family-display, sans-serif);
  font-weight: 600;
  font-size: 1.1rem;
  line-height: 1.2;
}

.mt-tile__desc {
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mt-tile__chev {
  flex: 0 0 auto;
  opacity: 0.5;
}
</style>
