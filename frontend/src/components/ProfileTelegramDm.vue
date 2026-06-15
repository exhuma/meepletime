<template>
  <div v-if="dmBots.length" class="mt-3">
    <v-alert
      v-if="error"
      type="error"
      class="mb-2"
      closable
      @click:close="error = ''"
      >{{ error }}</v-alert
    >
    <v-alert
      v-if="notice"
      type="success"
      class="mb-2"
      closable
      @click:close="notice = ''"
      >{{ notice }}</v-alert
    >

    <div v-for="bot in dmBots" :key="bot.config_id" class="dm-row mb-2">
      <div class="d-flex align-center">
        <div class="flex-grow-1">
          <div class="font-weight-medium">{{ bot.label }}</div>
          <div class="text-caption text-medium-emphasis">
            {{ bot.circle_name }} ·
            <span :class="bot.linked ? 'text-success' : ''">
              {{ bot.linked ? 'connected' : 'not connected' }}
            </span>
          </div>
        </div>
        <template v-if="bot.linked">
          <MtButton
            variant="soft"
            tone="primary"
            :loading="testingId === bot.config_id"
            @click="onTest(bot)"
          >
            Test
          </MtButton>
          <MtButton variant="ghost" tone="primary" @click="onUnlink(bot)">
            Disconnect
          </MtButton>
        </template>
        <MtButton
          v-else
          variant="soft"
          tone="primary"
          :loading="busyId === bot.config_id"
          @click="onDetect(bot)"
        >
          Connect
        </MtButton>
      </div>

      <template v-if="!bot.linked && detectingId === bot.config_id">
        <v-list v-if="detectOptions.length" density="compact" class="mt-1">
          <v-list-item
            v-for="opt in detectOptions"
            :key="opt.chat_id"
            :title="opt.name"
            :subtitle="opt.chat_id"
            @click="onPick(bot, opt.chat_id)"
          />
        </v-list>
        <p v-else class="text-caption text-medium-emphasis mt-1">
          No chat found yet. Open Telegram, start a chat with the bot and send
          it any message, then press Connect again.
        </p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Per-user Telegram DM opt-in shown on the profile page. Lists the
 * DM-mode bots of every circle the user belongs to and drives the
 * detect-and-pick connect flow.
 */
import { ref, onMounted } from 'vue'
import { useUserTelegram } from '../composables/useUserTelegram'
import { MtButton } from '../ui'
import type { TelegramChatOption, UserDmBot } from '../types'

const { dmBots, fetchDmBots, detectDmChats, linkDm, unlinkDm, testDm } =
  useUserTelegram()

const error = ref('')
const notice = ref('')
const busyId = ref<string | null>(null)
const testingId = ref<string | null>(null)
const detectingId = ref<string | null>(null)
const detectOptions = ref<TelegramChatOption[]>([])

onMounted(async () => {
  try {
    await fetchDmBots()
  } catch {
    error.value = 'Could not load your Telegram bots.'
  }
})

/** Detect the private chats a bot has seen, for the user to pick. */
async function onDetect(bot: UserDmBot): Promise<void> {
  error.value = ''
  busyId.value = bot.config_id
  detectingId.value = bot.config_id
  detectOptions.value = []
  try {
    detectOptions.value = await detectDmChats(bot.circle_id, bot.config_id)
  } catch {
    error.value = 'Could not reach Telegram for this bot.'
    detectingId.value = null
  } finally {
    busyId.value = null
  }
}

/** Link the chosen private chat to the bot. */
async function onPick(bot: UserDmBot, chatId: string): Promise<void> {
  error.value = ''
  try {
    await linkDm(bot.circle_id, bot.config_id, chatId)
    detectingId.value = null
    detectOptions.value = []
    notice.value = 'Connected. You will now receive direct messages.'
  } catch {
    error.value = 'Could not connect your Telegram chat.'
  }
}

/** Disconnect the user's DM link to a bot. */
async function onUnlink(bot: UserDmBot): Promise<void> {
  error.value = ''
  try {
    await unlinkDm(bot.circle_id, bot.config_id)
  } catch {
    error.value = 'Could not disconnect your Telegram chat.'
  }
}

/** Send a test DM for one bot. */
async function onTest(bot: UserDmBot): Promise<void> {
  error.value = ''
  notice.value = ''
  testingId.value = bot.config_id
  try {
    const result = await testDm(bot.circle_id, bot.config_id)
    if (result.ok) notice.value = result.message
    else error.value = result.message
  } catch {
    error.value = 'Could not send the test message.'
  } finally {
    testingId.value = null
  }
}
</script>

<style scoped>
.dm-row {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: var(--mt-field-radius, 8px);
  padding: 0.5rem 0.75rem;
}
</style>
