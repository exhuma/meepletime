/**
 * Long-press + tap gesture handler built on Pointer Events only.
 *
 * A primary tap fires `onTap`; holding past `delay` (or a desktop
 * right-click) fires `onLongPress`. Movement beyond `moveTolerance`
 * cancels the press so page scrolling is never hijacked. The synthetic
 * click that some browsers emit after a touch long-press is swallowed.
 *
 * Returns event handlers to bind on the target element. Pair with
 * `touch-action: pan-y` on that element so vertical scroll still works.
 */
import { onUnmounted } from 'vue'

interface LongPressOptions {
  onTap: () => void
  onLongPress: () => void
  delay?: number
  moveTolerance?: number
}

export function useLongPress(opts: LongPressOptions) {
  const delay = opts.delay ?? 500
  const moveTolerance = opts.moveTolerance ?? 10

  let timer: ReturnType<typeof setTimeout> | null = null
  let fired = false
  let suppressClick = false
  let startX = 0
  let startY = 0

  function clearTimer(): void {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function onPointerdown(ev: PointerEvent): void {
    // Fresh interaction: drop any stale click-suppression.
    suppressClick = false
    // Only the primary button starts a hold; right-click is handled
    // by the contextmenu event instead.
    if (ev.button !== 0) return
    fired = false
    startX = ev.clientX
    startY = ev.clientY
    clearTimer()
    timer = setTimeout(() => {
      timer = null
      fired = true
      suppressClick = true
      opts.onLongPress()
    }, delay)
  }

  function onPointermove(ev: PointerEvent): void {
    if (timer === null) return
    const dx = ev.clientX - startX
    const dy = ev.clientY - startY
    if (Math.hypot(dx, dy) > moveTolerance) clearTimer()
  }

  function onPointerup(): void {
    clearTimer()
  }

  function onPointercancel(): void {
    clearTimer()
  }

  function onContextmenu(ev: MouseEvent): void {
    ev.preventDefault()
    opts.onLongPress()
  }

  function onClick(ev: MouseEvent): void {
    if (suppressClick) {
      suppressClick = false
      ev.preventDefault()
      ev.stopPropagation()
      return
    }
    opts.onTap()
  }

  onUnmounted(clearTimer)

  return {
    onPointerdown,
    onPointermove,
    onPointerup,
    onPointercancel,
    onContextmenu,
    onClick,
  }
}
