<template>
  <v-container class="pa-4" fluid>
    <v-row justify="center">
      <v-col cols="12" sm="9" md="6" lg="5">
        <v-alert
          v-if="error"
          type="error"
          class="mb-4"
          closable
          @click:close="error = ''"
          >{{ error }}</v-alert
        >
        <v-alert
          v-if="notice"
          type="success"
          class="mb-4"
          closable
          @click:close="notice = ''"
          >{{ notice }}</v-alert
        >

        <MtCard class="ps-section mb-4">
          <h1 class="ps-section__title">Profile</h1>
          <p class="text-body-2 text-medium-emphasis mb-4">
            Your name and email come from your login. Upload a photo to
            personalise your avatar.
          </p>
          <ProfileAvatarField />
        </MtCard>

        <MtCard v-if="settings" class="ps-section">
          <h2 class="ps-section__title">Notifications</h2>
          <p class="text-body-2 text-medium-emphasis mb-5">
            Choose how MeepleTime tells you when a day becomes a viable meetup.
            You can mute individual circles separately.
          </p>

          <!-- Email row -->
          <div class="ps-row">
            <div class="ps-row__toggle">
              <v-switch
                v-model="emailEnabled"
                label="Email"
                color="primary"
                hide-details
                :disabled="saving"
                @update:model-value="onEmailChange"
              />
              <p class="text-caption text-medium-emphasis ps-row__hint">
                Emails go to your confirmed notification address, or your
                account email if none is set.
              </p>
            </div>
            <MtButton
              variant="soft"
              tone="primary"
              :loading="testing === 'email'"
              @click="onTest('email')"
            >
              Test
            </MtButton>
          </div>

          <!-- Notification email address. The field is an *override*:
               empty means "use the account email", shown below so the
               default address is never hidden. -->
          <div class="ps-email">
            <v-text-field
              v-model="emailInput"
              label="Use a different email (optional)"
              type="email"
              density="comfortable"
              :disabled="emailBusy"
              hide-details="auto"
              :placeholder="accountEmail ?? 'Use account email'"
              persistent-placeholder
            >
              <template v-if="emailIndicator" #append-inner>
                <v-icon
                  :color="emailIndicator.color"
                  :title="emailIndicator.title"
                >
                  {{ emailIndicator.icon }}
                </v-icon>
              </template>
            </v-text-field>
            <p class="text-caption text-medium-emphasis ps-email__help">
              Leave blank to use your account email<template
                v-if="accountEmail"
              >
                (<strong>{{ accountEmail }}</strong
                >)</template
              >. A different address must be confirmed before it is used.
            </p>

            <div class="ps-email__actions">
              <MtButton
                v-if="emailIsNew"
                variant="solid"
                tone="primary"
                :loading="emailBusy"
                @click="onSaveEmail"
              >
                Send confirmation
              </MtButton>
              <MtButton
                v-if="pendingEmail"
                variant="soft"
                tone="primary"
                :loading="emailBusy"
                @click="onResendEmail"
              >
                Resend link
              </MtButton>
              <MtButton
                v-if="confirmedEmail || pendingEmail"
                variant="ghost"
                tone="primary"
                :loading="emailBusy"
                @click="onClearEmail"
              >
                Use account email
              </MtButton>
            </div>
            <p v-if="emailMessage" class="text-caption ps-email__msg">
              {{ emailMessage }}
            </p>
          </div>

          <v-divider class="my-3" />

          <!-- Browser-push row -->
          <div class="ps-row">
            <div class="ps-row__toggle">
              <v-switch
                v-model="webpushEnabled"
                label="Browser notifications (this device)"
                color="primary"
                hide-details
                :disabled="saving || !webpushSupported"
                @update:model-value="onWebpushChange"
              />
              <p class="text-caption text-medium-emphasis ps-row__hint">
                <template v-if="!webpushSupported">
                  This browser does not support background notifications.
                </template>
                <template v-else>
                  Shows a system notification even when the tab is closed.
                  Enable once per device.
                </template>
              </p>
            </div>
            <MtButton
              variant="soft"
              tone="primary"
              :disabled="!webpushSupported"
              :loading="testing === 'webpush'"
              @click="onTest('webpush')"
            >
              Test
            </MtButton>
          </div>

          <v-divider class="my-3" />

          <!-- Telegram row -->
          <div class="ps-row">
            <div class="ps-row__toggle">
              <v-switch
                v-model="telegramDmEnabled"
                label="Telegram direct messages"
                color="primary"
                hide-details
                :disabled="saving"
                @update:model-value="onTelegramDmChange"
              />
              <p class="text-caption text-medium-emphasis ps-row__hint">
                Master switch for personal Telegram direct messages. A circle's
                bot must also be linked to your account to receive them.
              </p>
            </div>
            <MtButton
              variant="soft"
              tone="primary"
              :loading="testing === 'telegram'"
              @click="onTest('telegram')"
            >
              Test
            </MtButton>
          </div>
        </MtCard>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useNotificationSettings } from '../composables/useNotificationSettings'
import { useAuth } from '../composables/auth'
import { useAppBarContext, useAppBar } from '../composables/appBar'
import { isWebPushSupported } from '../lib/webpush'
import { ApiError } from '../api'
import { MtCard, MtButton } from '../ui'
import ProfileAvatarField from '../components/ProfileAvatarField.vue'

useAppBarContext('Profile')

const {
  settings,
  fetchSettings,
  updateSettings,
  subscribeWebPush,
  unsubscribeWebPush,
  testChannel,
  setNotificationEmail,
  resendNotificationEmail,
  clearNotificationEmail,
} = useNotificationSettings()
const { startJob, endJob } = useAppBar()
const { accountEmail } = useAuth()

const error = ref('')
const notice = ref('')
const testing = ref<'email' | 'webpush' | 'telegram' | null>(null)
const saving = ref(false)
const emailEnabled = ref(false)
const webpushEnabled = ref(false)
const telegramDmEnabled = ref(false)
const webpushSupported = isWebPushSupported()

const emailInput = ref('')
const emailBusy = ref(false)
const emailMessage = ref('')

const confirmedEmail = computed(
  () => settings.value?.notification_email ?? null,
)
const pendingEmail = computed(() => settings.value?.pending_email ?? null)

/** The trimmed override the user has typed (empty ⇒ account email). */
const trimmedInput = computed(() => emailInput.value.trim())

/**
 * True when the typed address is a brand-new one that has not yet been
 * sent for confirmation — the only state where "Send confirmation"
 * applies.
 */
const emailIsNew = computed(
  () =>
    trimmedInput.value !== '' &&
    trimmedInput.value !== confirmedEmail.value &&
    trimmedInput.value !== pendingEmail.value,
)

/**
 * A compact status icon for the field, replacing the verbose chips:
 * a confirmed address shows a check, a pending one shows a clock, and
 * anything else (empty or unsent) shows nothing.
 */
const emailIndicator = computed<{
  icon: string
  color: string
  title: string
} | null>(() => {
  if (trimmedInput.value === '') return null
  if (trimmedInput.value === confirmedEmail.value) {
    return {
      icon: 'mdi-check-circle',
      color: 'success',
      title: 'Confirmed — notifications use this address.',
    }
  }
  if (trimmedInput.value === pendingEmail.value) {
    return {
      icon: 'mdi-clock-alert-outline',
      color: 'warning',
      title: 'Awaiting confirmation — check your inbox.',
    }
  }
  return null
})

onMounted(async () => {
  startJob('profile-settings')
  try {
    await fetchSettings()
    emailEnabled.value = settings.value?.email_enabled ?? false
    webpushEnabled.value = settings.value?.webpush_enabled ?? false
    telegramDmEnabled.value = settings.value?.telegram_dm_enabled ?? false
    emailInput.value = settings.value?.notification_email ?? ''
  } catch {
    error.value = 'Could not load your notification settings.'
  } finally {
    endJob('profile-settings')
  }
})

async function onTest(
  channel: 'email' | 'webpush' | 'telegram',
): Promise<void> {
  error.value = ''
  notice.value = ''
  testing.value = channel
  try {
    const result = await testChannel(channel)
    if (result.ok) notice.value = result.message
    else error.value = result.message
  } catch {
    error.value = 'Could not send the test notification.'
  } finally {
    testing.value = null
  }
}

async function onTelegramDmChange(value: boolean | null): Promise<void> {
  saving.value = true
  try {
    await updateSettings({ telegram_dm_enabled: !!value })
  } catch (e: unknown) {
    error.value =
      e instanceof ApiError
        ? 'Could not save your change. Please try again.'
        : 'Something went wrong.'
    telegramDmEnabled.value = settings.value?.telegram_dm_enabled ?? false
  } finally {
    saving.value = false
  }
}

async function onSaveEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await setNotificationEmail(emailInput.value.trim())
    emailMessage.value = 'Confirmation link sent. Check your inbox.'
  } catch {
    emailMessage.value = 'Could not send the confirmation link.'
  } finally {
    emailBusy.value = false
  }
}

async function onResendEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await resendNotificationEmail()
    emailMessage.value = 'A new confirmation link is on its way.'
  } catch {
    emailMessage.value = 'Could not resend the link just yet.'
  } finally {
    emailBusy.value = false
  }
}

async function onClearEmail(): Promise<void> {
  emailBusy.value = true
  emailMessage.value = ''
  try {
    await clearNotificationEmail()
    emailInput.value = ''
    emailMessage.value = 'Notifications will use your account email.'
  } catch {
    emailMessage.value = 'Could not clear the address.'
  } finally {
    emailBusy.value = false
  }
}

async function onEmailChange(value: boolean | null): Promise<void> {
  saving.value = true
  try {
    await updateSettings({ email_enabled: !!value })
  } catch (e: unknown) {
    error.value =
      e instanceof ApiError
        ? 'Could not save your change. Please try again.'
        : 'Something went wrong.'
    // Revert the toggle to the last known server state.
    emailEnabled.value = settings.value?.email_enabled ?? false
  } finally {
    saving.value = false
  }
}

async function onWebpushChange(value: boolean | null): Promise<void> {
  saving.value = true
  try {
    if (value) {
      await subscribeWebPush()
    } else {
      await unsubscribeWebPush()
    }
  } catch (e: unknown) {
    if (e instanceof Error && e.message === 'webpush-unconfigured') {
      error.value = 'Browser notifications are not available on this server.'
    } else if (e instanceof Error && e.message === 'permission-denied') {
      error.value = 'Notification permission was denied by the browser.'
    } else {
      error.value = 'Could not change browser notifications.'
    }
    // Revert the toggle to the last known server state.
    webpushEnabled.value = settings.value?.webpush_enabled ?? false
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.ps-section {
  padding: 1.5rem;
}

.ps-section__title {
  font-family: var(--v-font-family-display, 'Noto Serif', serif);
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 0.35rem;
}

/* Each channel row: toggle+hint on the left, Test button on the right. */
.ps-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.ps-row__toggle {
  flex: 1 1 0;
  min-width: 0;
}

.ps-row__hint {
  margin-top: 0.15rem;
  margin-bottom: 0;
}

.ps-email {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ps-email__help {
  margin: 0;
}
.ps-email__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.ps-email__msg {
  color: rgb(var(--v-theme-on-surface-variant, 120 120 120));
}
</style>
