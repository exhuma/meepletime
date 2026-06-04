<template>
  <div>
    <!-- TODO - viability status indicator should be added to the app-bar
    <v-app-bar elevation="1" color="surface">
      <v-chip
        v-if="viability"
        :color="viability.is_viable ? 'primary' : 'error'"
        size="small"
        class="mr-3"
      >
        {{ viability.is_viable ? 'Viable' : 'Not Viable' }}
      </v-chip>
    </v-app-bar>
    -->
    <v-container class="pa-4" style="max-width: 600px">
      <div class="mb-6">
        <h3 class="text-subtitle-1 font-weight-bold mb-2">Attendees</h3>
        <v-list
          v-if="enrichedAttendees.length > 0"
          lines="one"
          class="rounded-lg"
          elevation="1"
        >
          <v-list-item v-for="a in enrichedAttendees" :key="a.user_id">
            <template #prepend>
              <v-icon
                :color="a.state === 'hosting' ? 'primary' : 'secondary'"
                class="mr-2"
              >
                {{ a.state === 'hosting' ? 'mdi-home' : 'mdi-calendar-check' }}
              </v-icon>
            </template>
            <v-list-item-title>{{ a.pseudonym }}</v-list-item-title>
            <v-list-item-subtitle class="text-capitalize">{{
              a.state
            }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <v-alert v-else type="info" density="compact"
          >No attendees yet.</v-alert
        >
      </div>

      <div>
        <h3 class="text-subtitle-1 font-weight-bold mb-2">Notes</h3>
        <div v-if="notes.length > 0" class="mb-4">
          <v-card
            v-for="note in notes"
            :key="note.id"
            class="mb-2"
            variant="tonal"
          >
            <v-card-text class="pa-3">
              <div class="d-flex justify-space-between mb-1">
                <span class="text-caption font-weight-bold">{{
                  note.pseudonym || 'User'
                }}</span>
                <span class="text-caption text-medium-emphasis">{{
                  formatTime(note.created_at)
                }}</span>
              </div>
              <p class="text-body-2 mb-0">{{ note.content }}</p>
            </v-card-text>
          </v-card>
        </div>
        <v-alert v-else type="info" density="compact" class="mb-4"
          >No notes yet.</v-alert
        >

        <v-form @submit.prevent="submitNote">
          <v-textarea
            v-model="newNote"
            label="Add a note..."
            rows="3"
            variant="outlined"
            hide-details
            class="mb-2"
          />
          <v-btn
            type="submit"
            color="primary"
            :loading="submitting"
            :disabled="!newNote.trim()"
            block
          >
            Add Note
          </v-btn>
        </v-form>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { format, parseISO } from 'date-fns'
import { useCircles } from '../composables/circles'
import type { Note } from '../types'
import { useAppBar, useAppBarContext } from '../composables/appBar'

const route = useRoute()
const { startJob, endJob } = useAppBar()
const circlesState = useCircles()

const circleId = route.params.id as string
const date = route.params.date as string

const submitting = ref(false)
const notes = ref<Note[]>([])
const newNote = ref('')

const formattedDate = computed<string>(() => {
  try {
    return format(parseISO(date), 'EEEE, MMMM d, yyyy')
  } catch {
    return date
  }
})

const attendees = computed(() => circlesState.calendar.value[date] ?? [])
const viability = computed(() => circlesState.viability.value[date] ?? null)

useAppBarContext(formattedDate.value, [])

/** Cross-reference attendees with the members list to resolve pseudonyms. */
const enrichedAttendees = computed(() =>
  attendees.value.map((a) => {
    const member = circlesState.members.value.find(
      (m) => m.user_id === a.user_id,
    )
    return { ...a, pseudonym: member?.pseudonym ?? a.user_id }
  }),
)

/** Format an ISO timestamp string to a short human-readable form. */
function formatTime(ts: string): string {
  if (!ts) return ''
  try {
    return format(new Date(ts), 'MMM d, HH:mm')
  } catch {
    return ts
  }
}

/** Submit a new note for the current day. */
async function submitNote(): Promise<void> {
  if (!newNote.value.trim()) return
  submitting.value = true
  try {
    const note = await circlesState.addNote(
      circleId,
      date,
      newNote.value.trim(),
    )
    notes.value = [...notes.value, note]
    newNote.value = ''
  } catch (e) {
    console.error('Add note error', e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  startJob('loading-day-detail-view')
  try {
    const [fetchedNotes] = await Promise.all([
      circlesState.fetchNotes(circleId, date),
      circlesState.fetchCircle(circleId),
      circlesState.fetchMembers(circleId),
      circlesState.fetchCalendar(circleId, date, date),
      circlesState.fetchViability(circleId, date, date),
    ])
    notes.value = fetchedNotes
  } catch (e) {
    console.error('Load error', e)
  } finally {
    endJob('loading-day-detail-view')
  }
})
</script>
