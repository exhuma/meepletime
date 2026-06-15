import { ref, readonly } from 'vue'
import type { DeepReadonly, Ref } from 'vue'
import api from '../api'
import type {
  NotificationTestResult,
  TelegramChatOption,
  UserDmBot,
} from '../types'

// Module-level state: DM bots offered to the current user, across all
// circles they belong to.
const dmBots = ref<UserDmBot[]>([])

/**
 * Per-user Telegram DM opt-in. Aggregates the DM-mode bots of every
 * circle the user is a member of, and drives the detect-and-pick link
 * flow against the existing per-circle endpoints.
 */
export function useUserTelegram() {
  /** Fetch the DM bots available to the current user. */
  async function fetchDmBots(): Promise<void> {
    dmBots.value = await api.get<UserDmBot[]>('/users/me/telegram/dm-bots')
  }

  /** List the private chats a DM bot has recently seen. */
  async function detectDmChats(
    circleId: string,
    configId: string,
  ): Promise<TelegramChatOption[]> {
    const res = await api.post<{ chats: TelegramChatOption[] }>(
      `/circles/${circleId}/telegram/${configId}/detect-dm`,
    )
    return res.chats
  }

  /** Link the caller's private chat id to a DM-mode bot. */
  async function linkDm(
    circleId: string,
    configId: string,
    chatId: string,
  ): Promise<void> {
    await api.put(`/circles/${circleId}/telegram/${configId}/link`, {
      chat_id: chatId,
    })
    dmBots.value = dmBots.value.map((b) =>
      b.config_id === configId ? { ...b, linked: true } : b,
    )
  }

  /** Remove the caller's DM link to a bot. */
  async function unlinkDm(circleId: string, configId: string): Promise<void> {
    await api.delete(`/circles/${circleId}/telegram/${configId}/link`)
    dmBots.value = dmBots.value.map((b) =>
      b.config_id === configId ? { ...b, linked: false } : b,
    )
  }

  /** Send a real test DM for one bot and return the result. */
  async function testDm(
    circleId: string,
    configId: string,
  ): Promise<NotificationTestResult> {
    return api.post<NotificationTestResult>(
      `/circles/${circleId}/telegram/${configId}/test`,
    )
  }

  return {
    dmBots: readonly(dmBots) as DeepReadonly<Ref<UserDmBot[]>>,
    fetchDmBots,
    detectDmChats,
    linkDm,
    unlinkDm,
    testDm,
  }
}
