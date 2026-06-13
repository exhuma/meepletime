<template>
  <v-app>
    <v-app-bar flat>
      <v-progress-linear
        v-if="isBusy"
        color="primary"
        indeterminate
        absolute
        location="bottom"
      />
      <template v-if="auth.isLoggedIn.value">
        <v-avatar
          size="34"
          color="primary"
          class="app-avatar ml-2 hidden-md-and-up"
        >
          <span class="text-caption font-weight-bold">{{ userInitial }}</span>
        </v-avatar>
        <MtButton
          variant="icon"
          tone="primary"
          icon="mdi-logout"
          class="hidden-md-and-up"
          @click="handleLogout"
        />
      </template>

      <MtButton
        variant="icon"
        tone="primary"
        icon="mdi-arrow-left"
        @click="router.back()"
      />

      <v-app-bar-title>
        <span class="brand">
          <span class="brand__logo text-primary"><MtMeeple /></span>
          <span class="brand__name">MeepleTime</span>
          <template v-if="title">
            <span class="brand__sep">·</span>
            <span class="brand__ctx">{{ title }}</span>
          </template>
        </span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <MtButton
        v-for="action in actions"
        :key="action.label"
        variant="icon"
        tone="primary"
        :icon="action.icon"
        :title="action.label"
        class="mr-1"
        @click="action.action()"
      />

      <MtButton
        v-if="auth.isLoggedIn.value"
        variant="icon"
        tone="primary"
        icon="mdi-cog"
        title="Notification settings"
        @click="router.push('/profile')"
      />

      <template v-if="auth.isLoggedIn.value">
        <v-avatar
          size="34"
          color="primary"
          class="app-avatar hidden-sm-and-down"
        >
          <span class="text-caption font-weight-bold">{{ userInitial }}</span>
        </v-avatar>
        <MtButton
          variant="icon"
          tone="primary"
          icon="mdi-logout"
          class="hidden-sm-and-down"
          @click="handleLogout"
        />
      </template>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuth } from './composables/auth'
import { useAppBar } from './composables/appBar'
import { useRouter } from 'vue-router'
import { MtButton } from './ui'
import MtMeeple from './ui/MtMeeple.vue'

const { title, actions, isBusy } = useAppBar()

const auth = useAuth()
const router = useRouter()

onMounted(async () => {
  await auth.loadFromStorage()
})

const userInitial = computed<string>(() => {
  const name =
    auth.oidcUser.value?.profile?.name ??
    auth.oidcUser.value?.profile?.email ??
    ''
  return (name as string).charAt(0).toUpperCase() || '?'
})

/** Sign out the current user via OIDC. */
async function handleLogout(): Promise<void> {
  await auth.logout()
}
</script>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.brand__logo {
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
}

.brand__name {
  font-family: var(--v-font-family-display, sans-serif);
  font-weight: 600;
}

.brand__sep {
  opacity: 0.45;
}

.brand__ctx {
  font-weight: 500;
  opacity: 0.85;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-avatar {
  color: rgb(var(--v-theme-on-primary));
}
</style>
