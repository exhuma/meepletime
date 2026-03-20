<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-4" elevation="4">
          <v-card-title class="text-h5 text-center mb-2">Create Account</v-card-title>
          <v-card-subtitle class="text-center mb-4">Join MeepleTime</v-card-subtitle>
          <v-card-text>
            <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
              {{ error }}
            </v-alert>
            <v-alert v-if="success" type="success" class="mb-4">
              Account created! <router-link to="/login">Sign in</router-link>
            </v-alert>
            <v-form @submit.prevent="handleRegister" v-if="!success">
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
                class="mb-3"
                required
                autocomplete="new-password"
              />
              <v-text-field
                v-model="confirmPassword"
                label="Confirm Password"
                :type="showPassword ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock-check"
                variant="outlined"
                :error-messages="passwordMismatch ? ['Passwords do not match'] : []"
                class="mb-4"
                required
                autocomplete="new-password"
              />
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="passwordMismatch"
              >
                Create Account
              </v-btn>
            </v-form>
          </v-card-text>
          <v-card-actions class="justify-center">
            <span class="text-body-2">Already have an account?</span>
            <v-btn variant="text" color="primary" to="/login" class="ml-1">Sign In</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref(false)

const passwordMismatch = computed(() =>
  confirmPassword.value.length > 0 && password.value !== confirmPassword.value
)

async function handleRegister() {
  if (passwordMismatch.value) return
  error.value = ''
  loading.value = true
  try {
    await auth.register(email.value, password.value)
    success.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
