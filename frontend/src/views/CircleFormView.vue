<template>
  <v-container class="pa-4" style="max-width: 720px">
    <h1 class="text-h5 mb-4">
      {{ isEdit ? 'Edit circle' : 'Create a circle' }}
    </h1>

    <v-alert
      v-if="error"
      type="error"
      class="mb-4"
      closable
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>
    <v-alert v-if="isEdit && !isAdmin" type="info" variant="tonal" class="mb-4">
      Only an owner or admin can change circle settings.
    </v-alert>

    <v-form @submit.prevent="handleSubmit">
      <CircleFormFields :form="form" />
      <CircleImageField
        v-model:file="imageFile"
        v-model:remove="removeImage"
        :current-image-ref="currentCircle?.image_ref"
      />

      <!-- Per-circle notification config (admin-gated), mirroring the old
           edit dialog. Only meaningful once the circle exists. -->
      <v-expansion-panels v-if="isEdit && isAdmin" class="mt-4">
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon class="mr-2" color="primary">mdi-bell-cog</v-icon>
            Notifications — Telegram
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <CircleTelegramAdmin :circle-id="circleId" />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <div class="form-actions">
        <MtButton variant="ghost" tone="primary" @click="onCancel">
          Cancel
        </MtButton>
        <MtButton
          type="submit"
          tone="primary"
          :loading="loading"
          :disabled="!canSubmit"
        >
          {{ isEdit ? 'Save' : 'Create' }}
        </MtButton>
      </div>
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import { useAuth } from '../composables/auth'
import { useAppBar } from '../composables/appBar'
import { isAdminOrOwner } from '../lib/members'
import { ApiError } from '../api'
import { MtButton } from '../ui'
import CircleFormFields from '../components/CircleFormFields.vue'
import type { CircleFormModel } from '../components/CircleFormFields.vue'
import CircleImageField from '../components/CircleImageField.vue'
import CircleTelegramAdmin from '../components/CircleTelegramAdmin.vue'

const route = useRoute()
const router = useRouter()
const circles = useCircles()
const auth = useAuth()
const { startJob, endJob } = useAppBar()

/** Edit mode carries a circle id in the route; create mode does not. */
const circleId = (route.params.id as string | undefined) ?? ''
const isEdit = computed<boolean>(() => !!circleId)
const { currentCircle, members } = circles

const loading = ref(false)
const error = ref('')
const imageFile = ref<File | null>(null)
const removeImage = ref(false)

const form = reactive<CircleFormModel>({
  name: '',
  description: '',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  host_needed: false,
  minimum_attendees: null,
  soft_max_attendees: null,
  hard_max_attendees: null,
})

/** True when the current user may edit this circle (always so on create). */
const isAdmin = computed<boolean>(() =>
  isAdminOrOwner(members.value, auth.userId.value),
)

/** A name is always required; edits additionally need edit rights. */
const canSubmit = computed<boolean>(
  () => !!form.name.trim() && (!isEdit.value || isAdmin.value),
)

/** Copy the loaded circle into the editable form (edit mode). */
function syncFromCircle(): void {
  const c = currentCircle.value
  if (!c) return
  form.name = c.name
  form.description = c.description ?? ''
  form.timezone = c.timezone
  form.host_needed = c.host_needed
  form.minimum_attendees = c.minimum_attendees
  form.soft_max_attendees = c.soft_max_attendees
  form.hard_max_attendees = c.hard_max_attendees
}

onMounted(async () => {
  if (!isEdit.value) return
  startJob('load-circle-form')
  try {
    // Reuse already-loaded data where possible; otherwise fetch it.
    if (currentCircle.value?.id !== circleId) {
      await circles.fetchCircle(circleId)
    }
    if (members.value.length === 0) {
      await circles.fetchMembers(circleId)
    }
    syncFromCircle()
  } catch {
    error.value = 'Failed to load circle.'
  } finally {
    endJob('load-circle-form')
  }
})

/** Shared payload for create/update from the current form state. */
function payload() {
  return {
    name: form.name.trim(),
    description: form.description || null,
    timezone: form.timezone,
    host_needed: form.host_needed,
    minimum_attendees: form.minimum_attendees || null,
    soft_max_attendees: form.soft_max_attendees || null,
    hard_max_attendees: form.hard_max_attendees || null,
  }
}

async function handleSubmit(): Promise<void> {
  if (!canSubmit.value) return
  error.value = ''
  loading.value = true
  try {
    if (isEdit.value) {
      await circles.updateCircle(circleId, payload())
      // Image is stored separately; a new file wins over a remove.
      if (imageFile.value) {
        await circles.uploadCircleImage(circleId, imageFile.value)
      } else if (removeImage.value) {
        await circles.deleteCircleImage(circleId)
      }
      router.push(`/circles/${circleId}`)
    } else {
      const created = await circles.createCircle(payload())
      // The new circle must exist before its image can be attached.
      if (imageFile.value) {
        await circles.uploadCircleImage(created.id, imageFile.value)
      }
      router.push(`/circles/${created.id}`)
    }
  } catch (e: unknown) {
    const detail =
      e instanceof ApiError
        ? (e.data as { detail?: string } | null)?.detail
        : null
    error.value =
      detail ?? (isEdit.value ? 'Failed to save circle.' : 'Failed to create.')
  } finally {
    loading.value = false
  }
}

/** Return to the circle (edit) or the circles list (create). */
function onCancel(): void {
  router.push(isEdit.value ? `/circles/${circleId}` : '/circles')
}
</script>

<style scoped>
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
</style>
