<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-4" elevation="4">
          <v-card-title class="text-h5 text-center mb-2">Welcome Back</v-card-title>
          <v-card-subtitle class="text-center mb-4">Sign in to MeepleTime</v-card-subtitle>
          <v-card-text>
            <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
              {{ error }}
            </v-alert>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email"
                type="email"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                class="mb-3"
                required
                autocomplete="email"
              />
              <v-text-field
                v-model="password"
                label="Password"
                :type="showPassword ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                variant="outlined"
                class="mb-4"
                required
                autocomplete="current-password"
              />
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
              >
                Sign In
              </v-btn>
            </v-form>
          </v-card-text>
          <v-card-actions class="justify-center">
            <span class="text-body-2">Don't have an account?</span>
            <v-btn variant="text" color="primary" to="/register" class="ml-1">Register</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>
