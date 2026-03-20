<template>
  <v-container class="pa-4" max-width="600">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h6 font-weight-bold">My Circles</h2>
      <v-spacer />
      <v-btn variant="text" color="primary" @click="joinDialog = true" size="small">
        <v-icon start>mdi-key</v-icon> Join
      </v-btn>
    </div>

    <v-progress-circular v-if="loading" indeterminate color="primary" class="d-block mx-auto my-8" />

    <v-alert v-if="!loading && circlesState.circles.value.length === 0" type="info" class="mb-4">
      You're not in any circles yet. Create one or join with an invite token!
    </v-alert>

    <v-list v-if="!loading && circlesState.circles.value.length > 0" lines="two" class="mb-4">
      <v-list-item
        v-for="circle in circlesState.circles.value"
        :key="circle.id"
        :to="`/circles/${circle.id}`"
        rounded="lg"
        class="mb-2"
        elevation="1"
      >
        <template #prepend>
          <v-avatar color="primary" size="44">
            <v-icon color="white">mdi-account-group</v-icon>
          </v-avatar>
        </template>
        <v-list-item-title class="font-weight-semibold">{{ circle.name }}</v-list-item-title>
        <v-list-item-subtitle>{{ circle.description || 'No description' }}</v-list-item-subtitle>
        <template #append>
          <v-icon>mdi-chevron-right</v-icon>
        </template>
      </v-list-item>
    </v-list>

    <v-btn color="primary" size="large" block prepend-icon="mdi-plus" @click="createDialog = true">
      Create Circle
    </v-btn>

    <CreateCircleDialog v-model="createDialog" @created="onCircleCreated" />

    <v-dialog v-model="joinDialog" max-width="400">
      <v-card>
        <v-card-title>Join a Circle</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="joinToken"
            label="Invite Token"
            prepend-inner-icon="mdi-key"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="joinDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="goToJoin" :disabled="!joinToken">Join</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCircles } from '../composables/circles'
import CreateCircleDialog from '../components/CreateCircleDialog.vue'

const circlesState = useCircles()
const router = useRouter()

const loading = ref(false)
const createDialog = ref(false)
const joinDialog = ref(false)
const joinToken = ref('')

onMounted(async () => {
  loading.value = true
  try {
    await circlesState.fetchCircles()
  } finally {
    loading.value = false
  }
})

/** Close the create dialog after a circle has been created. */
function onCircleCreated(): void {
  createDialog.value = false
}

/** Navigate to the join page for the entered invite token. */
function goToJoin(): void {
  if (joinToken.value) {
    joinDialog.value = false
    router.push(`/join/${joinToken.value}`)
  }
}
</script>
