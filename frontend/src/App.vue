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
        <v-avatar size="32" class="hidden-md-and-up">
          <span class="text-caption font-weight-bold">
            {{ userInitial }}
          </span>
        </v-avatar>
        <v-btn icon @click="handleLogout" class="hidden-md-and-up">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </template>

      <v-btn icon @click="router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>

      <v-app-bar-title>
        <span class="font-weight-bold">MeepleTime - {{ title }}</span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <v-btn
        v-for="action in actions"
        :key="action.label"
        icon
        :title="action.label"
        @click="action.action()"
        class="mr-1"
      >
        <v-icon>{{ action.icon }}</v-icon>
      </v-btn>

      <template v-if="auth.isLoggedIn.value">
        <v-avatar size="32" class="hidden-sm-and-down">
          <span class="text-caption font-weight-bold">
            {{ userInitial }}
          </span>
        </v-avatar>
        <v-btn icon @click="handleLogout" class="hidden-sm-and-down">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
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
