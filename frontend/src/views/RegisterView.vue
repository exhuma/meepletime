<template>
  <v-container class="fill-height pa-4" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-4" elevation="4">
          <v-card-title class="text-h6 mb-4">Create Account</v-card-title>
          <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
            {{ error }}
          </v-alert>
          <v-alert v-if="success" type="success" class="mb-4">
            Account created! You can now sign in.
          </v-alert>
          <v-form @submit.prevent="handleRegister">
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
              class="mb-3"
              required
            />
            <v-text-field
              v-model="confirmPassword"
              label="Confirm Password"
              type="password"
              variant="outlined"
              class="mb-4"
              required
            />
            <v-btn type="submit" color="primary" size="large" block :loading="loading">
              Register
            </v-btn>
          </v-form>
          <div class="text-center mt-4">
            <router-link to="/login">Already have an account? Sign in</router-link>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuth } from '../composables/auth'

const auth = useAuth()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

/** Validate the form and submit the registration request. */
async function handleRegister(): Promise<void> {
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await auth.register(email.value, password.value)
    success.value = true
  } catch {
    error.value = 'Registration failed. The email may already be in use.'
  } finally {
    loading.value = false
  }
}
</script>
