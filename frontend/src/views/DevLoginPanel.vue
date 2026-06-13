<template>
  <div>
    <p class="mt-5 text-medium-emphasis">
      Development login — pick an identity
    </p>
    <MtButton
      v-for="p in presets"
      :key="p.sub"
      tone="primary"
      block
      class="my-2"
      :loading="pending === p.sub"
      @click="selectPreset(p)"
    >
      {{ p.name }}
    </MtButton>
  </div>
</template>

<script setup lang="ts">
/**
 * Dev-only login picker (no Keycloak).
 *
 * Loaded lazily by LoginView behind a static `import.meta.env.DEV`
 * guard, so Rollup drops this entire chunk — and its `/auth/dev/login`
 * call and helper imports — from any production build.
 *
 * The preset identities below are a developer convenience and the
 * authoritative copy lives in `docs/developer/auth.md`. They are
 * defined here (dev-only code) rather than fetched from the API, so
 * the backend never enumerates dev credentials.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'
import { devLogin, type DevIdentity } from '../auth/devLogin'
import { MtButton } from '../ui'

const props = defineProps<{ returnTo: string }>()
const router = useRouter()
const auth = useAuth()

// Distinct identities for exercising RBAC. The labels are only
// identity hints — roles are per-circle, so "admin" has no global
// powers until it owns/joins a circle (see docs/developer/auth.md).
const presets: DevIdentity[] = [
  { sub: 'dev-owner', email: 'dev-owner@meepletime.local', name: 'Dev Owner' },
  { sub: 'dev-admin', email: 'dev-admin@meepletime.local', name: 'Dev Admin' },
  {
    sub: 'dev-member',
    email: 'dev-member@meepletime.local',
    name: 'Dev Member',
  },
]

const pending = ref<string | null>(null)

/** Log in as the chosen identity, then continue to the destination. */
async function selectPreset(identity: DevIdentity): Promise<void> {
  pending.value = identity.sub
  try {
    await devLogin(identity)
    await auth.loadFromStorage()
    await router.replace(props.returnTo)
  } finally {
    pending.value = null
  }
}
</script>
