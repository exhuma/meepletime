import { ref, readonly } from 'vue'
import type { DeepReadonly, Ref } from 'vue'
import api from '../api'
import type {
  CircleTelegramConfig,
  NotificationTestResult,
  TelegramChatOption,
  TelegramDmBot,
} from '../types'

// Module-level state for the circle currently being managed.
const configs = ref<CircleTelegramConfig[]>([])
const dmBots = ref<TelegramDmBot[]>([])

interface TelegramConfigInput {
  label: string
  bot_token: string
  mode?: 'group' | 'dm'
  group_chat_id?: string | null
}

/** Return reactive circle-Telegram state and actions (owner/admin). */
export function useCircleTelegram() {
  /** Fetch the circle's Telegram bot configs (tokens masked). */
  async function fetchConfigs(circleId: string): Promise<void> {
    configs.value = await api.get<CircleTelegramConfig[]>(
      `/circles/${circleId}/telegram`,
    )
  }

  /** Register a new Telegram bot on the circle. */
  async function createConfig(
    circleId: string,
    payload: TelegramConfigInput,
  ): Promise<void> {
    const created = await api.post<CircleTelegramConfig>(
      `/circles/${circleId}/telegram`,
      payload,
    )
    configs.value = [...configs.value, created]
  }

  /** Apply a partial update to a bot config. */
  async function updateConfig(
    circleId: string,
    configId: string,
    patch: Partial<TelegramConfigInput>,
  ): Promise<void> {
    const updated = await api.put<CircleTelegramConfig>(
      `/circles/${circleId}/telegram/${configId}`,
      patch,
    )
    configs.value = configs.value.map((c) => (c.id === configId ? updated : c))
  }

  /** Remove a bot config from the circle. */
  async function deleteConfig(
    circleId: string,
    configId: string,
  ): Promise<void> {
    await api.delete(`/circles/${circleId}/telegram/${configId}`)
    configs.value = configs.value.filter((c) => c.id !== configId)
  }

  /** Ask the bot which chats it has recently seen (for chat-id pick). */
  async function detectChats(
    circleId: string,
    configId: string,
  ): Promise<TelegramChatOption[]> {
    const res = await api.post<{ chats: TelegramChatOption[] }>(
      `/circles/${circleId}/telegram/${configId}/detect-chat`,
    )
    return res.chats
  }

  /** Fetch DM-mode bots in the circle with the caller's link state. */
  async function fetchDmBots(circleId: string): Promise<void> {
    dmBots.value = await api.get<TelegramDmBot[]>(
      `/circles/${circleId}/telegram/dm-bots`,
    )
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
      b.id === configId ? { ...b, linked: true } : b,
    )
  }

  /** Remove the caller's DM link to a bot. */
  async function unlinkDm(circleId: string, configId: string): Promise<void> {
    await api.delete(`/circles/${circleId}/telegram/${configId}/link`)
    dmBots.value = dmBots.value.map((b) =>
      b.id === configId ? { ...b, linked: false } : b,
    )
  }

  /** Send a real test message for one bot and return the result. */
  async function testConfig(
    circleId: string,
    configId: string,
  ): Promise<NotificationTestResult> {
    return api.post<NotificationTestResult>(
      `/circles/${circleId}/telegram/${configId}/test`,
    )
  }

  return {
    configs: readonly(configs) as DeepReadonly<Ref<CircleTelegramConfig[]>>,
    dmBots: readonly(dmBots) as DeepReadonly<Ref<TelegramDmBot[]>>,
    fetchConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    detectChats,
    fetchDmBots,
    linkDm,
    unlinkDm,
    testConfig,
  }
}
