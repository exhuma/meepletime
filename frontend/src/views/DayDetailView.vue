<template>
  <div>
    <v-app-bar elevation="1" color="white">
      <v-btn icon @click="router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title>{{ formattedDate }}</v-app-bar-title>
      <v-chip
        v-if="viability"
        :color="viability.is_viable ? 'green' : 'red'"
        text-color="white"
        size="small"
        class="mr-3"
      >
        {{ viability.is_viable ? 'Viable' : 'Not Viable' }}
      </v-chip>
    </v-app-bar>

    <v-container class="pa-4" style="max-width:600px">
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" />

      <!-- Attendees -->
      <div class="mb-6">
        <h3 class="text-subtitle-1 font-weight-bold mb-2">Attendees</h3>
        <v-list v-if="enrichedAttendees.length > 0" lines="one" class="rounded-lg" elevation="1">
          <v-list-item
            v-for="a in enrichedAttendees"
            :key="a.user_id"
          >
            <template #prepend>
              <v-icon :color="a.state === 'hosting' ? 'green' : 'blue'" class="mr-2">
                {{ a.state === 'hosting' ? 'mdi-home' : 'mdi-calendar-check' }}
              </v-icon>
            </template>
            <v-list-item-title>{{ a.pseudonym }}</v-list-item-title>
            <v-list-item-subtitle class="text-capitalize">{{ a.state }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <v-alert v-else type="info" density="compact">No attendees yet.</v-alert>
      </div>

      <!-- Notes -->
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
                <span class="text-caption font-weight-bold">{{ note.pseudonym || 'User' }}</span>
                <span class="text-caption text-grey">{{ formatTime(note.created_at) }}</span>
              </div>
              <p class="text-body-2 mb-0">{{ note.content }}</p>
            </v-card-text>
          </v-card>
        </div>
        <v-alert v-else type="info" density="compact" class="mb-4">No notes yet.</v-alert>

        <!-- Add note form -->
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

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { format, parseISO } from 'date-fns'
import { useCirclesStore } from '../stores/circles'

const route = useRoute()
const router = useRouter()
const circles = useCirclesStore()

const circleId = route.params.id
const date = route.params.date

const loading = ref(false)
const submitting = ref(false)
const notes = ref([])
const newNote = ref('')

const formattedDate = computed(() => {
  try {
    return format(parseISO(date), 'EEEE, MMMM d, yyyy')
  } catch {
    return date
  }
})

const attendees = computed(() => circles.calendar[date] || [])
const viability = computed(() => circles.viability[date] || null)

// Cross-reference attendees with membership list for pseudonyms
const enrichedAttendees = computed(() => {
  return attendees.value.map(a => {
    const member = circles.members.find(m => m.user_id === a.user_id)
    return { ...a, pseudonym: member?.pseudonym || a.user_id }
  })
})

function formatTime(ts) {
  if (!ts) return ''
  try {
    return format(new Date(ts), 'MMM d, HH:mm')
  } catch {
    return ts
  }
}

async function submitNote() {
  if (!newNote.value.trim()) return
  submitting.value = true
  try {
    const note = await circles.addNote(circleId, date, newNote.value.trim())
    notes.value.push(note)
    newNote.value = ''
  } catch (e) {
    console.error('Add note error', e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [fetchedNotes] = await Promise.all([
      circles.fetchNotes(circleId, date),
      circles.fetchCircle(circleId),
      circles.fetchMembers(circleId),
      circles.fetchCalendar(circleId, date, date),
      circles.fetchViability(circleId, date, date),
    ])
    notes.value = fetchedNotes
  } catch (e) {
    console.error('Load error', e)
  } finally {
    loading.value = false
  }
})
</script>
