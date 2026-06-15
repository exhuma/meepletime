<!--
  Non-intrusive build-identity strip: the app version and a link to
  the source repository. Aimed at debugging sessions, not core UI, so
  it sits at reduced opacity (full on hover) with a small font.

  - Version comes from the build-time __APP_VERSION__ constant
    (see vite.config.ts).
  - The GitHub link follows the module-github-link kit: shown only
    when VITE_GITHUB_REPO_URL is set, opened in a new tab with
    rel="noopener noreferrer", never sourced from user input.
-->
<template>
  <footer
    v-if="version || repoUrl"
    class="app-footer text-caption text-medium-emphasis"
  >
    <span v-if="version">{{ version }}</span>
    <a
      v-if="repoUrl"
      class="app-footer__link"
      :href="repoUrl"
      target="_blank"
      rel="noopener noreferrer"
      title="Source code"
    >
      <v-icon icon="mdi-github" size="14" />
      <span>Source code</span>
    </a>
  </footer>
</template>

<script setup lang="ts">
const version: string = __APP_VERSION__
const repoUrl: string | undefined = import.meta.env.VITE_GITHUB_REPO_URL
</script>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  padding: 4px 12px;
  opacity: 0.4;
}

.app-footer:hover {
  opacity: 1;
}

.app-footer__link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: inherit;
  text-decoration: none;
}
</style>
