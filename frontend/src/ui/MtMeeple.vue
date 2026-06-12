<template>
  <svg class="mt-meeple" viewBox="0 0 64 64" aria-hidden="true">
    <circle cx="32" cy="13" r="8.5" />
    <path
      d="M32 23c-6.2 0-10 3.4-12 8-1.5 3.4-6.5 3.6-6.5 8 0 2.6
         2.6 3.8 5.4 2.8 1.8-.64 3.4-1.8 4.6-3-.2 4.2-2 8.6-2
         13.4h21c0-4.8-1.8-9.2-2-13.4 1.2 1.2 2.8 2.36 4.6 3 2.8
         1 5.4-.2 5.4-2.8 0-4.4-5-4.6-6.5-8-2-4.6-5.8-8-12-8z"
    />
  </svg>
</template>

<script setup lang="ts">
/** The MeepleTime mascot: a wooden player token. Inherits currentColor. */
</script>

<style scoped>
.mt-meeple {
  width: 100%;
  height: 100%;
  display: block;
  fill: currentColor;
}
</style>
