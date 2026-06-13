/**
 * Browser-side Web Push helpers.
 *
 * Thin glue around the Service Worker and Push APIs. All backend
 * communication lives in the notification-settings composable; this
 * module only deals with the browser primitives.
 */

/** Return whether this browser supports background Web Push. */
export function isWebPushSupported(): boolean {
  return (
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  )
}

/** Convert a base64url VAPID key to the Uint8Array the API expects. */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const output = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i)
  }
  return output
}

/** Register the service worker and resolve once it is active. */
async function ensureRegistration(): Promise<ServiceWorkerRegistration> {
  const registration = await navigator.serviceWorker.register('/sw.js')
  await navigator.serviceWorker.ready
  return registration
}

/**
 * Subscribe this device for Web Push and return the JSON payload.
 *
 * Requests notification permission if not already granted.
 */
export async function browserSubscribe(
  vapidPublicKey: string,
): Promise<PushSubscriptionJSON> {
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') {
    throw new Error('permission-denied')
  }
  const registration = await ensureRegistration()
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  })
  return subscription.toJSON()
}

/** Return the current push subscription for this device, if any. */
export async function getBrowserSubscription(): Promise<PushSubscription | null> {
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) return null
  return registration.pushManager.getSubscription()
}
