<template>
  <div class="avatar-field">
    <v-avatar size="96" color="primary" class="avatar-field__preview">
      <v-img
        v-if="avatarUrl && !imgError"
        :src="avatarUrl"
        alt="Your profile picture"
        @error="imgError = true"
      />
      <span v-else class="text-h5 font-weight-bold">{{ initial }}</span>
    </v-avatar>

    <div class="avatar-field__controls">
      <v-file-input
        v-model="file"
        label="Upload a photo"
        accept="image/png,image/jpeg,image/webp"
        prepend-icon="mdi-camera"
        variant="outlined"
        density="comfortable"
        hide-details="auto"
        :disabled="busy"
        :error-messages="error ? [error] : []"
        @update:model-value="onSelect"
      />
      <div class="avatar-field__row">
        <MtButton
          v-if="hasUpload"
          variant="ghost"
          tone="primary"
          size="small"
          icon="mdi-trash-can-outline"
          :loading="busy"
          @click="onRemove"
        >
          Remove photo
        </MtButton>
      </div>
      <p class="text-caption text-medium-emphasis mb-0">
        Falls back to your provider photo or a gravatar, then your initials.
        JPEG, PNG, or WebP · up to 5&nbsp;MB.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Profile-picture picker for the settings page. Shows the resolved
 * avatar (uploaded image, provider photo, gravatar, or initials) and
 * uploads a chosen file immediately via the auth composable.
 */
import { computed, ref } from 'vue'
import { useAuth } from '../composables/auth'
import { resolveImageUrl, validateImageFile } from '../lib/circleImage'
import { MtButton } from '../ui'

const auth = useAuth()

const file = ref<File | null>(null)
const error = ref('')
const busy = ref(false)
const imgError = ref(false)

/** Browser-loadable URL for the current resolved avatar. */
const avatarUrl = computed(() => resolveImageUrl(auth.avatarRef.value))

/** True when the current avatar is a user-uploaded image. */
const hasUpload = computed(
  () => auth.avatarRef.value?.startsWith('/users/') ?? false,
)

/** First initial for the fallback avatar. */
const initial = computed<string>(() => {
  const name =
    auth.oidcUser.value?.profile?.name ??
    auth.oidcUser.value?.profile?.email ??
    ''
  return (name as string).charAt(0).toUpperCase() || '?'
})

/** Validate then immediately upload the chosen file. */
async function onSelect(value: File | File[] | null): Promise<void> {
  error.value = ''
  const chosen = Array.isArray(value) ? (value[0] ?? null) : value
  if (!chosen) return
  const message = validateImageFile(chosen)
  if (message) {
    error.value = message
    file.value = null
    return
  }
  busy.value = true
  try {
    await auth.uploadAvatar(chosen)
    imgError.value = false
  } catch {
    error.value = 'Could not upload your photo. Please try again.'
  } finally {
    busy.value = false
    file.value = null
  }
}

/** Remove the uploaded photo and fall back through the chain. */
async function onRemove(): Promise<void> {
  error.value = ''
  busy.value = true
  try {
    await auth.removeAvatar()
    imgError.value = false
  } catch {
    error.value = 'Could not remove your photo. Please try again.'
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.avatar-field {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}
.avatar-field__preview {
  color: rgb(var(--v-theme-on-primary));
  flex: 0 0 auto;
}
.avatar-field__controls {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.avatar-field__row {
  min-height: 0;
}
</style>
