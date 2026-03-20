<template>
  <v-app>
    <v-app-bar color="primary" elevation="2">
      <v-app-bar-title>
        <span class="font-weight-bold">MeepleTime</span>
      </v-app-bar-title>
      <template v-if="auth.isLoggedIn.value">
        <v-avatar color="secondary" size="32" class="mr-2">
          <span class="text-caption font-weight-bold">{{ userInitial }}</span>
        </v-avatar>
        <v-btn icon @click="handleLogout">
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
import { useRouter } from 'vue-router'
import { useAuth } from './composables/auth'

const auth = useAuth()
const router = useRouter()

onMounted(() => {
  auth.loadFromStorage()
})

const userInitial = computed<string>(() => {
  const email = auth.user.value?.email ?? ''
  return email.charAt(0).toUpperCase() || '?'
})

/** Sign out the current user and navigate to the login page. */
function handleLogout(): void {
  auth.logout()
  router.push('/login')
}
</script>
