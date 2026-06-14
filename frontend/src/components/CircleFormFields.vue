<template>
  <div>
    <v-text-field
      v-model="form.name"
      label="Circle Name"
      variant="outlined"
      required
      class="mb-3"
    />
    <v-textarea
      v-model="form.description"
      label="Description (optional)"
      variant="outlined"
      rows="2"
      class="mb-3"
    />
    <v-autocomplete
      v-model="form.timezone"
      label="Timezone"
      :items="timezones"
      hint="The time-zone the events in this circle will be scheduled in."
      persistent-hint
      variant="outlined"
      class="mb-3"
    />
    <v-checkbox
      v-model="form.host_needed"
      label="This circle requires a host"
      hint="At least one member must host to make events viable."
      persistent-hint
      color="primary"
      class="mb-3"
    />
    <v-row>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model.number="form.minimum_attendees"
          label="Min attendees"
          type="number"
          variant="outlined"
          min="1"
          hint="The number of participants needed to make a session viable."
          persistent-hint
          clearable
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model.number="form.soft_max_attendees"
          label="Soft max"
          type="number"
          variant="outlined"
          min="1"
          hint="The number of participants at which a sessions feels crowded"
          persistent-hint
          clearable
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model.number="form.hard_max_attendees"
          label="Hard max"
          type="number"
          variant="outlined"
          min="1"
          hint="The maximum number of participants a session can support."
          persistent-hint
          clearable
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
/**
 * Shared circle settings fields used by both the create and edit
 * dialogs. The parent owns the reactive ``form`` object; this
 * component binds directly to it (passed by reference).
 */

/** Editable circle settings shared by create and edit flows. */
export interface CircleFormModel {
  name: string
  description: string
  timezone: string
  host_needed: boolean
  minimum_attendees: number | null
  soft_max_attendees: number | null
  hard_max_attendees: number | null
}

defineProps<{ form: CircleFormModel }>()

const timezones = Intl.supportedValuesOf('timeZone')
</script>
