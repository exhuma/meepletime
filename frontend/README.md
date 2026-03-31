# Frontend

The frontend visual system is derived from the Keycloak login theme.

## Brand tokens

Brand colors, fonts, and shared shape tokens live in
`../design/meepletime-brand.json`.

Run the token exporter after updating that file:

```bash
npm run brand:sync
```

That command regenerates:

- `src/generated/brand-theme.ts` for Vuetify theme setup
- `src/generated/brand-tokens.css` for shared frontend CSS tokens
- `../assets/keycloak/themes/meepletime/login/resources/css/brand-tokens.css`

Keep `login.ftl` handwritten. The shared source of truth is the token
set, not the rendered markup.# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).
