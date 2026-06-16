<template>
  <div ref="el" class="rte"></div>
</template>

<script setup lang="ts">
/**
 * Minimal Quill editor bound to a Delta document.
 *
 * The toolbar is constrained to the formats the backend accepts for a
 * day description (bold/italic/underline, ordered/bullet lists, links,
 * h3/h4 headings). `v-model` carries the Quill Delta verbatim.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Quill from 'quill'
import 'quill/dist/quill.snow.css'
import type { DeltaDoc } from '../types'

const props = defineProps<{ modelValue: DeltaDoc | null }>()
const emit = defineEmits<{ 'update:modelValue': [DeltaDoc] }>()

const el = ref<HTMLDivElement | null>(null)
let quill: Quill | null = null
// Guards re-entrancy when we set contents programmatically.
let applying = false

const TOOLBAR = [
  ['bold', 'italic', 'underline'],
  [{ header: 3 }, { header: 4 }],
  [{ list: 'ordered' }, { list: 'bullet' }],
  ['link'],
  ['clean'],
]
const FORMATS = ['bold', 'italic', 'underline', 'header', 'list', 'link']

function setContents(value: DeltaDoc | null): void {
  if (!quill) return
  applying = true
  quill.setContents(
    (value ?? { ops: [] }) as Parameters<Quill['setContents']>[0],
  )
  applying = false
}

onMounted(() => {
  if (!el.value) return
  quill = new Quill(el.value, {
    theme: 'snow',
    formats: FORMATS,
    modules: { toolbar: TOOLBAR },
    placeholder: 'Add session details…',
  })
  setContents(props.modelValue)
  quill.on('text-change', () => {
    if (applying || !quill) return
    emit('update:modelValue', quill.getContents() as unknown as DeltaDoc)
  })
})

watch(
  () => props.modelValue,
  (value) => {
    if (!quill || applying) return
    const current = JSON.stringify(quill.getContents())
    if (JSON.stringify(value ?? { ops: [] }) === current) return
    setContents(value)
  },
)

onBeforeUnmount(() => {
  quill = null
})
</script>

<style scoped>
.rte :deep(.ql-toolbar),
.rte :deep(.ql-container) {
  border-color: rgb(var(--v-theme-outline-variant));
}
.rte :deep(.ql-container) {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  font-family: inherit;
  font-size: 0.95rem;
  min-height: 120px;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}
.rte :deep(.ql-toolbar) {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}
.rte :deep(.ql-editor.ql-blank::before) {
  color: rgb(var(--v-theme-on-surface-variant));
  font-style: normal;
}
.rte :deep(.ql-stroke) {
  stroke: rgb(var(--v-theme-on-surface-variant));
}
.rte :deep(.ql-fill) {
  fill: rgb(var(--v-theme-on-surface-variant));
}
.rte :deep(.ql-active .ql-stroke) {
  stroke: rgb(var(--v-theme-primary));
}
</style>
