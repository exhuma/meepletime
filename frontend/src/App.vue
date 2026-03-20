<template>
  <v-app>
    <v-app-bar color="primary" elevation="2">
      <v-app-bar-title>
        <span class="font-weight-bold">MeepleTime</span>
      </v-app-bar-title>
      <template v-if="auth.isLoggedIn">
        <v-avatar color="secondary" size="32" class="mr-2">
          <span class="text-caption font-weight-bold">{{ userInitial }}</span>
        </v-avatar>
        <v-btn icon @click="auth.logout">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </template>
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()

onMounted(() => {
  auth.loadFromStorage()
})

const userInitial = computed(() => {
  if (!auth.user) return '?'
  const email = auth.user.sub || auth.user.email || ''
  return email.charAt(0).toUpperCase()
})
</script>
