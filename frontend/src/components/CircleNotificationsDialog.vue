<template>
  <MtDialog
    :model-value="modelValue"
    :max-width="520"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #title>
      <span class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-bell-cog</v-icon>
        Notifications — {{ circleName }}
      </span>
    </template>

    <v-alert
      v-if="error"
      type="error"
      class="mb-3"
      closable
      @click:close="error = ''"
      >{{ error }}</v-alert
    >
    <v-alert
      v-if="notice"
      type="success"
      class="mb-3"
      closable
      @click:close="notice = ''"
      >{{ notice }}</v-alert
    >

    <template v-if="isAdmin || dmBots.length">
      <h3 class="text-subtitle-1 mb-1">Telegram</h3>

      <template v-if="isAdmin">
        <p class="text-body-2 text-medium-emphasis mb-3">
          Add a bot (from BotFather) to post viability updates into a group
          chat. Add the bot to your group, send a message there, then use
          “Detect chat” to pick the chat id.
        </p>

        <div v-for="config in configs" :key="config.id" class="bot-row mb-3">
          <div class="d-flex align-center">
            <div class="flex-grow-1">
              <div class="font-weight-medium">{{ config.label }}</div>
              <div class="text-caption text-medium-emphasis">
                token {{ config.token_hint }} ·
                <template v-if="config.group_chat_id">
                  chat {{ config.group_chat_id }}
                </template>
                <span v-else class="text-warning">no chat yet</span>
              </div>
            </div>
            <MtButton
              variant="soft"
              tone="primary"
              :disabled="!config.group_chat_id"
              :loading="testingId === config.id"
              @click="onTest(config.id)"
            >
              Test
            </MtButton>
            <MtButton
              variant="soft"
              tone="primary"
              :loading="busyConfigId === config.id"
              @click="onDetect(config.id)"
            >
              Detect chat
            </MtButton>
            <MtButton
              variant="icon"
              tone="primary"
              icon="mdi-delete"
              title="Remove bot"
              @click="onRemove(config.id)"
            />
          </div>

          <v-list
            v-if="detectingId === config.id && detectOptions.length"
            density="compact"
            class="mt-1"
          >
            <v-list-item
              v-for="opt in detectOptions"
              :key="opt.chat_id"
              :title="opt.name"
              :subtitle="`${opt.type} · ${opt.chat_id}`"
              @click="onPickChat(config.id, opt.chat_id)"
            />
          </v-list>
          <p
            v-else-if="detectingId === config.id"
            class="text-caption text-medium-emphasis mt-1"
          >
            No chats seen yet. Add the bot to a group and post a message, then
            try again.
          </p>
        </div>

        <v-form class="mb-3" @submit.prevent="onCreate">
          <v-text-field
            v-model="newLabel"
            label="Bot label"
            variant="outlined"
            density="compact"
            hide-details
            class="mb-2"
          />
          <v-text-field
            v-model="newToken"
            label="Bot token (from BotFather)"
            variant="outlined"
            density="compact"
            hide-details
            class="mb-2"
          />
          <MtButton
            type="submit"
            tone="primary"
            :loading="creating"
            :disabled="!newLabel.trim() || !newToken.trim()"
          >
            Add bot
          </MtButton>
        </v-form>
      </template>

      <div v-if="dmBots.length">
        <v-divider v-if="isAdmin" class="my-3" />
        <h4 class="text-subtitle-2 mb-1">Your direct messages</h4>
        <p class="text-caption text-medium-emphasis mb-2">
          Get personal Telegram messages for this circle. Turn on Telegram DMs
          in your profile too, start a private chat with the bot, then enter
          your chat id (e.g. from @userinfobot).
        </p>
        <div v-for="bot in dmBots" :key="bot.id" class="bot-row mb-2">
          <div class="d-flex align-center">
            <div class="flex-grow-1">
              <div class="font-weight-medium">{{ bot.label }}</div>
              <div
                class="text-caption"
                :class="bot.linked ? 'text-success' : 'text-medium-emphasis'"
              >
                {{ bot.linked ? 'Linked' : 'Not linked' }}
              </div>
            </div>
            <template v-if="bot.linked">
              <MtButton
                variant="soft"
                tone="primary"
                :loading="testingId === bot.id"
                @click="onTest(bot.id)"
              >
                Test
              </MtButton>
              <MtButton variant="soft" tone="primary" @click="onUnlink(bot.id)">
                Unlink
              </MtButton>
            </template>
          </div>
          <div v-if="!bot.linked" class="d-flex align-center mt-1">
            <v-text-field
              v-model="dmChatInput[bot.id]"
              label="Your chat id"
              variant="outlined"
              density="compact"
              hide-details
              class="mr-2"
            />
            <MtButton
              tone="primary"
              :disabled="!(dmChatInput[bot.id] || '').trim()"
              @click="onLink(bot.id)"
            >
              Link
            </MtButton>
          </div>
        </div>
      </div>
    </template>

    <p v-else class="text-body-2 text-medium-emphasis">
      There is nothing to configure here for this circle yet.
    </p>

    <template #actions>
      <v-spacer />
      <MtButton
        variant="ghost"
        tone="primary"
        @click="$emit('update:modelValue', false)"
      >
        Close
      </MtButton>
    </template>
  </MtDialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCircleTelegram } from '../composables/useCircleTelegram'
import { MtDialog, MtButton } from '../ui'
import type { TelegramChatOption } from '../types'

const props = defineProps<{
  modelValue: boolean
  circleId: string
  circleName: string
  isAdmin: boolean
}>()

defineEmits<{ 'update:modelValue': [value: boolean] }>()

const {
  configs,
  dmBots,
  fetchConfigs,
  createConfig,
  updateConfig,
  deleteConfig,
  detectChats,
  fetchDmBots,
  linkDm,
  unlinkDm,
  testConfig,
} = useCircleTelegram()

const error = ref('')
const notice = ref('')
const creating = ref(false)
const newLabel = ref('')
const newToken = ref('')
const busyConfigId = ref<string | null>(null)
const testingId = ref<string | null>(null)
const detectingId = ref<string | null>(null)
const detectOptions = ref<TelegramChatOption[]>([])
const dmChatInput = ref<Record<string, string>>({})

async function load(): Promise<void> {
  error.value = ''
  notice.value = ''
  try {
    if (props.isAdmin) await fetchConfigs(props.circleId)
    await fetchDmBots(props.circleId)
  } catch {
    error.value = 'Could not load notification settings.'
  }
}

async function onTest(configId: string): Promise<void> {
  error.value = ''
  notice.value = ''
  testingId.value = configId
  try {
    const result = await testConfig(props.circleId, configId)
    if (result.ok) notice.value = result.message
    else error.value = result.message
  } catch {
    error.value = 'Could not send the test message.'
  } finally {
    testingId.value = null
  }
}

async function onLink(configId: string): Promise<void> {
  error.value = ''
  try {
    await linkDm(props.circleId, configId, dmChatInput.value[configId].trim())
    dmChatInput.value[configId] = ''
  } catch {
    error.value = 'Could not link your Telegram chat.'
  }
}

async function onUnlink(configId: string): Promise<void> {
  error.value = ''
  try {
    await unlinkDm(props.circleId, configId)
  } catch {
    error.value = 'Could not unlink your Telegram chat.'
  }
}

async function onCreate(): Promise<void> {
  creating.value = true
  error.value = ''
  try {
    await createConfig(props.circleId, {
      label: newLabel.value.trim(),
      bot_token: newToken.value.trim(),
    })
    newLabel.value = ''
    newToken.value = ''
  } catch {
    error.value = 'Could not add the bot.'
  } finally {
    creating.value = false
  }
}

async function onDetect(configId: string): Promise<void> {
  busyConfigId.value = configId
  error.value = ''
  detectingId.value = configId
  detectOptions.value = []
  try {
    detectOptions.value = await detectChats(props.circleId, configId)
  } catch {
    error.value = 'Could not reach Telegram for this bot.'
    detectingId.value = null
  } finally {
    busyConfigId.value = null
  }
}

async function onPickChat(configId: string, chatId: string): Promise<void> {
  error.value = ''
  try {
    await updateConfig(props.circleId, configId, { group_chat_id: chatId })
    detectingId.value = null
    detectOptions.value = []
  } catch {
    error.value = 'Could not set the chat id.'
  }
}

async function onRemove(configId: string): Promise<void> {
  error.value = ''
  try {
    await deleteConfig(props.circleId, configId)
  } catch {
    error.value = 'Could not remove the bot.'
  }
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) load()
  },
  { immediate: true },
)
</script>

<style scoped>
.bot-row {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: var(--mt-field-radius, 8px);
  padding: 0.5rem 0.75rem;
}
</style>
