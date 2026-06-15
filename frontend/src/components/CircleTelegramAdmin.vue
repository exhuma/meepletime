<template>
  <div>
    <p class="text-body-2 text-medium-emphasis mb-3">
      Add a bot (from BotFather) to send viability updates. A
      <strong>group chat</strong> bot posts to one shared chat; a
      <strong>direct messages</strong> bot lets members opt in to personal DMs
      from their own profile.
    </p>

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

    <div v-for="config in configs" :key="config.id" class="bot-row mb-3">
      <div class="d-flex align-center">
        <div class="flex-grow-1">
          <div class="font-weight-medium">{{ config.label }}</div>
          <div class="text-caption text-medium-emphasis">
            token {{ config.token_hint }} ·
            <template v-if="config.mode === 'dm'">
              direct messages · members opt in from their profile
            </template>
            <template v-else-if="config.group_chat_id">
              chat {{ config.group_chat_id }}
            </template>
            <span v-else class="text-warning">no chat yet</span>
          </div>
        </div>
        <template v-if="config.mode !== 'dm'">
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
        </template>
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
        No chats seen yet. Add the bot to a group and post a message, then try
        again.
      </p>
    </div>

    <v-form @submit.prevent="onCreate">
      <v-select
        v-model="newMode"
        :items="modeItems"
        label="Delivery mode"
        variant="outlined"
        density="compact"
        hide-details
        class="mb-2"
      />
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCircleTelegram } from '../composables/useCircleTelegram'
import { MtButton } from '../ui'
import type { TelegramChatOption } from '../types'

const props = defineProps<{ circleId: string }>()

const {
  configs,
  fetchConfigs,
  createConfig,
  updateConfig,
  deleteConfig,
  detectChats,
  testConfig,
} = useCircleTelegram()

const modeItems = [
  { title: 'Group chat', value: 'group' },
  { title: 'Direct messages', value: 'dm' },
]

const error = ref('')
const notice = ref('')
const creating = ref(false)
const newLabel = ref('')
const newToken = ref('')
const newMode = ref<'group' | 'dm'>('group')
const busyConfigId = ref<string | null>(null)
const testingId = ref<string | null>(null)
const detectingId = ref<string | null>(null)
const detectOptions = ref<TelegramChatOption[]>([])

onMounted(async () => {
  try {
    await fetchConfigs(props.circleId)
  } catch {
    error.value = 'Could not load notification settings.'
  }
})

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

async function onCreate(): Promise<void> {
  creating.value = true
  error.value = ''
  try {
    await createConfig(props.circleId, {
      label: newLabel.value.trim(),
      bot_token: newToken.value.trim(),
      mode: newMode.value,
    })
    newLabel.value = ''
    newToken.value = ''
    newMode.value = 'group'
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
</script>

<style scoped>
.bot-row {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: var(--mt-field-radius, 8px);
  padding: 0.5rem 0.75rem;
}
</style>
