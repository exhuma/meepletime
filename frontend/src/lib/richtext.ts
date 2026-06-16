/**
 * Render a Quill Delta document to HTML for read-only display.
 *
 * The Delta is the canonical stored representation; HTML is derived
 * here at render time and must always be passed through DOMPurify
 * before insertion into the DOM (see `RichTextView.vue`). A single
 * detached, module-level Quill instance does the conversion.
 */
import Quill from 'quill'
import type { DeltaDoc } from '../types'

let renderer: Quill | null = null

/** Convert a Delta document to its (unsanitized) HTML string. */
export function deltaToHtml(delta: DeltaDoc): string {
  if (typeof document === 'undefined') return ''
  if (!renderer) {
    const host = document.createElement('div')
    renderer = new Quill(host)
  }
  // Quill's setContents accepts a Delta/ops; our DeltaDoc mirrors that
  // shape but is typed structurally, so cast at the library boundary.
  renderer.setContents(delta as Parameters<Quill['setContents']>[0])
  return renderer.root.innerHTML
}
