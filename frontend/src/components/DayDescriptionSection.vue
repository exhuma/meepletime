<template>
  <div data-tour="day-detail-description">
    <h3 class="text-subtitle-1 font-weight-bold mb-2">
      {{ hostNeeded ? 'Host descriptions' : 'Description' }}
    </h3>

    <!-- Host-not-required: a single circle-wide description. -->
    <template v-if="!hostNeeded">
      <div v-if="!editingCircle">
        <div v-if="circleWide" class="dd-desc mb-2">
          <RichTextView :value="circleWide.content_delta" />
        </div>
        <p v-else class="dd-empty text-medium-emphasis mb-2">
          No description yet.
        </p>
        <div v-if="isAdmin" class="d-flex ga-2">
          <MtButton
            tone="primary"
            variant="soft"
            :icon="circleWide ? 'mdi-pencil' : 'mdi-plus'"
            @click="startEditCircle"
          >
            {{ circleWide ? 'Edit' : 'Add description' }}
          </MtButton>
          <MtButton
            v-if="circleWide"
            tone="danger"
            variant="ghost"
            icon="mdi-delete-outline"
            :loading="busy"
            @click="clearCircle"
          >
            Clear
          </MtButton>
        </div>
      </div>
      <div v-else>
        <RichTextEditor v-model="draft" class="mb-2" />
        <div class="d-flex ga-2">
          <MtButton
            tone="primary"
            icon="mdi-content-save"
            :loading="busy"
            :disabled="isDraftEmpty"
            @click="saveCircle"
          >
            Save
          </MtButton>
          <MtButton tone="primary" variant="ghost" @click="cancelEdit">
            Cancel
          </MtButton>
        </div>
      </div>
    </template>

    <!-- Host-required: one description per hosting member. -->
    <template v-else>
      <div v-if="otherEntries.length > 0" class="mb-3">
        <v-card
          v-for="entry in otherEntries"
          :key="entry.id"
          class="mb-2"
          variant="tonal"
        >
          <v-card-text class="pa-3">
            <div class="text-caption font-weight-bold mb-1">
              {{ entry.host_pseudonym || 'Host' }}
            </div>
            <RichTextView :value="entry.content_delta" />
          </v-card-text>
        </v-card>
      </div>

      <div v-if="amHosting">
        <div v-if="!editingMine">
          <div v-if="myEntry" class="dd-desc mb-2">
            <RichTextView :value="myEntry.content_delta" />
          </div>
          <p v-else class="dd-empty text-medium-emphasis mb-2">
            You have not described your session yet.
          </p>
          <div class="d-flex ga-2">
            <MtButton
              tone="primary"
              variant="soft"
              :icon="myEntry ? 'mdi-pencil' : 'mdi-plus'"
              @click="startEditMine"
            >
              {{ myEntry ? 'Edit my description' : 'Describe my session' }}
            </MtButton>
            <MtButton
              v-if="myEntry"
              tone="danger"
              variant="ghost"
              icon="mdi-delete-outline"
              :loading="busy"
              @click="clearMine"
            >
              Clear
            </MtButton>
          </div>
        </div>
        <div v-else>
          <RichTextEditor v-model="draft" class="mb-2" />
          <div class="d-flex ga-2">
            <MtButton
              tone="primary"
              icon="mdi-content-save"
              :loading="busy"
              :disabled="isDraftEmpty"
              @click="saveMine"
            >
              Save
            </MtButton>
            <MtButton tone="primary" variant="ghost" @click="cancelEdit">
              Cancel
            </MtButton>
          </div>
        </div>
      </div>
      <p
        v-else-if="otherEntries.length === 0"
        class="dd-empty text-medium-emphasis"
      >
        No host descriptions yet.
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * The day-description section. Renders a single circle-wide
 * description (owner/admin editable) for circles that do not require a
 * host, or one description per hosting member (each editable by its
 * own host) for host-required circles.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useCircles } from '../composables/circles'
import RichTextEditor from './RichTextEditor.vue'
import RichTextView from './RichTextView.vue'
import { MtButton } from '../ui'
import type { DayDescription, DeltaDoc } from '../types'

const props = defineProps<{
  circleId: string
  date: string
  hostNeeded: boolean
  isAdmin: boolean
  amHosting: boolean
  currentUserId: string | undefined
}>()

const circlesState = useCircles()

const circleWide = ref<DayDescription | null>(null)
const perHost = ref<DayDescription[]>([])
const editingCircle = ref(false)
const editingMine = ref(false)
const draft = ref<DeltaDoc | null>(null)
const busy = ref(false)

const myEntry = computed<DayDescription | null>(
  () =>
    perHost.value.find((h) => h.host_user_id === props.currentUserId) ?? null,
)
const otherEntries = computed<DayDescription[]>(() =>
  perHost.value.filter((h) => h.host_user_id !== props.currentUserId),
)

const isDraftEmpty = computed<boolean>(() => deltaText(draft.value) === '')

/** Concatenated plain text of a Delta, used to detect empty drafts. */
function deltaText(delta: DeltaDoc | null): string {
  if (!delta) return ''
  return (delta.ops as Array<{ insert?: unknown }>)
    .map((op) => (typeof op.insert === 'string' ? op.insert : ''))
    .join('')
    .trim()
}

function clone(delta: DeltaDoc | null): DeltaDoc | null {
  return delta ? (JSON.parse(JSON.stringify(delta)) as DeltaDoc) : null
}

async function load(): Promise<void> {
  const bundle = await circlesState.fetchDayDescriptions(
    props.circleId,
    props.date,
  )
  circleWide.value = bundle.circle_wide
  perHost.value = bundle.per_host
}

function startEditCircle(): void {
  draft.value = clone(circleWide.value?.content_delta ?? null)
  editingCircle.value = true
}

function startEditMine(): void {
  draft.value = clone(myEntry.value?.content_delta ?? null)
  editingMine.value = true
}

function cancelEdit(): void {
  editingCircle.value = false
  editingMine.value = false
  draft.value = null
}

async function saveCircle(): Promise<void> {
  if (!draft.value) return
  busy.value = true
  try {
    await circlesState.saveCircleDescription(
      props.circleId,
      props.date,
      draft.value,
    )
    await load()
    cancelEdit()
  } catch (e) {
    console.error('Save description error', e)
  } finally {
    busy.value = false
  }
}

async function clearCircle(): Promise<void> {
  busy.value = true
  try {
    await circlesState.clearCircleDescription(props.circleId, props.date)
    await load()
  } catch (e) {
    console.error('Clear description error', e)
  } finally {
    busy.value = false
  }
}

async function saveMine(): Promise<void> {
  if (!draft.value) return
  busy.value = true
  try {
    await circlesState.saveMyHostDescription(
      props.circleId,
      props.date,
      draft.value,
    )
    await load()
    cancelEdit()
  } catch (e) {
    console.error('Save host description error', e)
  } finally {
    busy.value = false
  }
}

async function clearMine(): Promise<void> {
  busy.value = true
  try {
    await circlesState.clearMyHostDescription(props.circleId, props.date)
    await load()
  } catch (e) {
    console.error('Clear host description error', e)
  } finally {
    busy.value = false
  }
}

// Reload when the day changes (the section is reused across routes).
watch(
  () => [props.circleId, props.date],
  () => {
    cancelEdit()
    void load()
  },
)

onMounted(() => {
  void load()
})
</script>

<style scoped>
.dd-desc {
  padding: 0.75rem 1rem;
  background: rgb(var(--v-theme-surface-container));
  border-radius: var(--mt-card-radius);
}
.dd-empty {
  padding: 0.75rem 1rem;
  background: rgb(var(--v-theme-surface-container));
  border-radius: var(--mt-card-radius);
  font-size: 0.9rem;
}
</style>
