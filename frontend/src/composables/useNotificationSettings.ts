import { ref, readonly } from 'vue'
import type { DeepReadonly, Ref } from 'vue'
import api from '../api'
import type { NotificationSettings, NotificationTestResult } from '../types'
import { browserSubscribe, getBrowserSubscription } from '../lib/webpush'

// Module-level singleton state for the current user's settings.
const settings = ref<NotificationSettings | null>(null)

/** Return reactive notification-settings state and actions. */
export function useNotificationSettings() {
  /** Fetch the current user's notification settings. */
  async function fetchSettings(): Promise<void> {
    settings.value = await api.get<NotificationSettings>(
      '/notifications/settings',
    )
  }

  /** Apply a partial update and store the returned settings. */
  async function updateSettings(
    patch: Partial<NotificationSettings>,
  ): Promise<void> {
    settings.value = await api.put<NotificationSettings>(
      '/notifications/settings',
      patch,
    )
  }

  /** Fetch the server's VAPID public key (null when unconfigured). */
  async function getVapidKey(): Promise<string | null> {
    const res = await api.get<{ vapid_public_key: string | null }>(
      '/notifications/webpush/key',
    )
    return res.vapid_public_key
  }

  /**
   * Subscribe this device for Web Push and enable the channel.
   *
   * Throws 'webpush-unconfigured' when the server has no VAPID key,
   * or 'permission-denied' when the user blocks notifications.
   */
  async function subscribeWebPush(): Promise<void> {
    const key = await getVapidKey()
    if (!key) throw new Error('webpush-unconfigured')
    const sub = await browserSubscribe(key)
    if (!sub.endpoint || !sub.keys) throw new Error('subscribe-failed')
    await api.post('/notifications/webpush/subscriptions', {
      endpoint: sub.endpoint,
      keys: { p256dh: sub.keys.p256dh, auth: sub.keys.auth },
    })
    await updateSettings({ webpush_enabled: true })
  }

  /** Unsubscribe this device and disable the channel. */
  async function unsubscribeWebPush(): Promise<void> {
    const sub = await getBrowserSubscription()
    if (sub) {
      const endpoint = encodeURIComponent(sub.endpoint)
      await api.delete(
        `/notifications/webpush/subscriptions?endpoint=${endpoint}`,
      )
      await sub.unsubscribe()
    }
    await updateSettings({ webpush_enabled: false })
  }

  /** Send a real test notification on one channel and return result. */
  async function testChannel(
    channel: 'email' | 'webpush' | 'telegram',
  ): Promise<NotificationTestResult> {
    return api.post<NotificationTestResult>('/notifications/test', {
      channel,
    })
  }

  return {
    settings: readonly(settings) as DeepReadonly<
      Ref<NotificationSettings | null>
    >,
    fetchSettings,
    updateSettings,
    subscribeWebPush,
    unsubscribeWebPush,
    testChannel,
  }
}
