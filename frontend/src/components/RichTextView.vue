<template>
  <div class="rtv" v-html="safeHtml"></div>
</template>

<script setup lang="ts">
/**
 * Read-only render of a Quill Delta description.
 *
 * Delta -> HTML (via Quill) -> DOMPurify -> `v-html`. The HTML is
 * always sanitized before it reaches the DOM; the stored Delta is
 * never trusted as markup.
 */
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import { deltaToHtml } from '../lib/richtext'
import type { DeltaDoc } from '../types'

const props = defineProps<{ value: DeltaDoc | null }>()

const safeHtml = computed<string>(() =>
  props.value ? DOMPurify.sanitize(deltaToHtml(props.value)) : '',
)
</script>

<style scoped>
.rtv {
  font-size: 0.95rem;
  line-height: 1.55;
  color: rgb(var(--v-theme-on-surface));
}
.rtv :deep(p) {
  margin: 0 0 0.5rem;
}
.rtv :deep(p:last-child) {
  margin-bottom: 0;
}
.rtv :deep(a) {
  color: rgb(var(--v-theme-primary));
}
</style>
