<template>
  <v-container class="fill-height pa-4" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-4" elevation="4">
          <v-card-title class="text-h6 mb-4">Sign In</v-card-title>
          <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
            {{ error }}
          </v-alert>
          <v-form @submit.prevent="handleLogin">
            <v-text-field
              v-model="email"
              label="Email"
              type="email"
              variant="outlined"
              class="mb-3"
              required
            />
            <v-text-field
              v-model="password"
              label="Password"
              type="password"
              variant="outlined"
              class="mb-4"
              required
            />
            <v-btn type="submit" color="primary" size="large" block :loading="loading">
              Sign In
            </v-btn>
          </v-form>
          <div class="text-center mt-4">
            <router-link to="/register">Don't have an account? Register</router-link>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/auth'

const auth = useAuth()
const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

/** Submit login credentials and navigate to /circles on success. */
async function handleLogin(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/circles')
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}
</script>
