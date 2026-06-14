/**
 * Helpers for circle hero images.
 *
 * Uploaded images are stored on the backend and referenced by an
 * API-relative path (e.g. ``/circles/<id>/image?v=<epoch>``). The
 * backend serves them from the API origin, so relative refs are
 * resolved against ``apiBaseUrl`` exactly as the fetch client does.
 * External absolute URLs and data URIs are used verbatim.
 */
import { apiBaseUrl } from '../config'

/** Accepted upload MIME types; mirrors the backend allow-list. */
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

/** Maximum upload size in bytes; mirrors the backend default. */
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024

/**
 * Resolve a stored ``image_ref`` to a browser-loadable URL.
 *
 * @param ref The persisted image reference, or null/empty.
 * @returns An absolute URL, or null when there is no image.
 */
export function resolveImageUrl(ref: string | null | undefined): string | null {
  if (!ref) return null
  if (/^https?:\/\//i.test(ref) || ref.startsWith('data:')) return ref
  return new URL(ref, apiBaseUrl).toString()
}

/**
 * Validate a selected file against the upload constraints.
 *
 * @param file The user-selected file.
 * @returns An error message, or null when the file is acceptable.
 */
export function validateImageFile(file: File): string | null {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return 'Please choose a JPEG, PNG, or WebP image.'
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return 'Image is too large (max 5 MB).'
  }
  return null
}
