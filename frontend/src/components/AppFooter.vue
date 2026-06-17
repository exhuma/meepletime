<!--
  Page footer. Two groups:
  - Legal links (Terms / Privacy) — reserved now, content to follow. The
    routes are public stubs so the links resolve even when logged out.
  - A non-intrusive build-identity strip: app version + source-repo link,
    kept at reduced opacity so it stays a debugging aid, not core UI.

  Rendered at the end of the scrollable content (see App.vue) rather than
  docked with `app`, because AppNav already docks a bottom navigation bar
  on small screens and two docked bottom bars would overlap.

  - Version comes from the build-time __APP_VERSION__ constant
    (see vite.config.ts).
  - The GitHub link follows the module-github-link kit: shown only when
    VITE_GITHUB_REPO_URL is set, opened in a new tab with
    rel="noopener noreferrer", never sourced from user input.
-->
<template>
  <v-footer class="app-footer">
    <nav class="app-footer__legal text-caption">
      <RouterLink class="app-footer__link" to="/legal/terms">
        Terms of Service
      </RouterLink>
      <span class="app-footer__sep" aria-hidden="true">·</span>
      <RouterLink class="app-footer__link" to="/legal/privacy">
        Privacy Policy
      </RouterLink>
    </nav>

    <v-spacer />

    <div
      v-if="version || repoUrl"
      class="app-footer__build text-caption text-medium-emphasis"
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
    </div>
  </v-footer>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

const version: string = __APP_VERSION__
const repoUrl: string | undefined = import.meta.env.VITE_GITHUB_REPO_URL
</script>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem 1rem;
  padding: 8px 16px;
}

.app-footer__legal {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* The build strip stays understated; legal links remain fully legible. */
.app-footer__build {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  opacity: 0.5;
}

.app-footer__build:hover {
  opacity: 1;
}

.app-footer__sep {
  opacity: 0.5;
}

.app-footer__link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: inherit;
  text-decoration: none;
}

.app-footer__link:hover {
  text-decoration: underline;
}
</style>
