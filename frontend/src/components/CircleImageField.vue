<template>
  <div class="mb-2">
    <div class="text-subtitle-2 mb-2">Hero image</div>

    <div v-if="previewUrl" class="image-field__preview mb-2">
      <img :src="previewUrl" alt="Circle hero preview" />
    </div>

    <v-file-input
      v-model="file"
      label="Upload an image"
      accept="image/png,image/jpeg,image/webp"
      prepend-icon="mdi-image"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      :error-messages="error ? [error] : []"
      @update:model-value="onSelect"
    />

    <div class="mt-1">
      <MtButton
        v-if="canRemove"
        variant="ghost"
        tone="primary"
        size="small"
        icon="mdi-trash-can-outline"
        @click="onRemove"
      >
        Remove image
      </MtButton>
    </div>
    <p class="text-caption text-medium-emphasis mb-0">
      JPEG, PNG, or WebP · up to 5&nbsp;MB.
    </p>
  </div>
</template>

<script setup lang="ts">
/**
 * Hero-image picker shared by the create and edit circle dialogs.
 *
 * Exposes two models: ``file`` (a newly chosen File, or null) and
 * ``remove`` (whether the existing image should be deleted on save).
 * The two are mutually exclusive — choosing a file clears the remove
 * intent and vice-versa.
 */
import { computed, ref, watch } from 'vue'
import { MtButton } from '../ui'
import { resolveImageUrl, validateImageFile } from '../lib/circleImage'

const props = defineProps<{
  /** Existing stored image reference, for preview (edit flow). */
  currentImageRef?: string | null
}>()

const file = defineModel<File | null>('file', { default: null })
const remove = defineModel<boolean>('remove', { default: false })

const error = ref('')
/** Object URL for a locally chosen file; revoked when replaced. */
const localUrl = ref<string | null>(null)

watch(file, (next, prev) => {
  if (prev && localUrl.value) {
    URL.revokeObjectURL(localUrl.value)
    localUrl.value = null
  }
  if (next) {
    localUrl.value = URL.createObjectURL(next)
  }
})

/** Validate the selection; reject and clear on failure. */
function onSelect(value: File | File[] | null): void {
  error.value = ''
  const chosen = Array.isArray(value) ? (value[0] ?? null) : value
  if (chosen) {
    const message = validateImageFile(chosen)
    if (message) {
      error.value = message
      file.value = null
      return
    }
    remove.value = false
  }
}

/** Mark the existing image for removal on save. */
function onRemove(): void {
  file.value = null
  remove.value = true
}

/** The currently resolved existing image URL, if any. */
const existingUrl = computed(() => resolveImageUrl(props.currentImageRef))

/** What to show in the preview pane. */
const previewUrl = computed<string | null>(() => {
  if (localUrl.value) return localUrl.value
  if (remove.value) return null
  return existingUrl.value
})

/** Whether a "remove" affordance makes sense. */
const canRemove = computed<boolean>(
  () => !remove.value && (!!file.value || !!existingUrl.value),
)
</script>

<style scoped>
.image-field__preview img {
  width: 100%;
  max-height: 160px;
  object-fit: cover;
  border-radius: 12px;
  display: block;
}
</style>
