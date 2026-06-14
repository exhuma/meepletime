# Stitch-aligned Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-skin the MeepleTime SPA to the Stitch "Warmer Dark" identity and add a desktop two-pane shell, changing presentation only — no backend, API, auth, routing-behavior, or domain-logic changes.

**Architecture:** The token layer (`theme/tokens.ts` + `tokens.css`) is the single source of truth and re-skins the whole app in one step; the `Mt*` façade components and all `lib/*`/composables/`api` logic are reused. Visual tasks restyle existing views in place; only the calendar and circle-card screens get structural rework. Two small pieces of new *logic* (last-viewed-circle tracking, per-circle next-viable-day derivation) are pure functions and get real unit tests (TDD).

**Tech Stack:** Vue 3 `<script setup lang="ts">`, Vuetify 3, Vite, vue-router, date-fns, Vitest (frontend unit tests), Playwright (visual verification via dev-login bypass), mdi icons.

**Reference:** Design spec at `docs/superpowers/specs/2026-06-14-stitch-redesign-design.md`. Stitch screenshots downloaded under `/tmp/stitch/*.png` and source HTML under `/tmp/stitch/*.html` (re-download from the Stitch MCP if absent).

---

## Conventions for every task

- **Branch:** all work lands on `stitch-redesign` (already checked out).
- **80-char line limit** on all files (`pre-commit` runs prettier on
  `frontend/`).
- **Verification is visual** for restyle tasks: after a change, drive the SPA
  with the Playwright dev-login bypass and screenshot the screen at mobile
  (390px) and desktop (1280px) widths, comparing against the matching
  `/tmp/stitch/*.png`. Setup for the dev harness:
  - Backend: `MEEPLETIME_DEV_AUTH_ENABLED=true` + `MEEPLETIME_DEV_SHARED_SECRET=devsecret` then `task backend`; DB via `task dev:db`.
  - Frontend: `VITE_DEV_AUTH=true task frontend`.
  - Navigate to `http://localhost:5173/login`, pick a dev identity, create/seed a circle with availability so the calendar has colored days.
- **Existing tests must stay green:** the suite lives in `frontend/tests/lib/`
  (invite, datetime, members, calendar, availability, viability). Run
  `cd frontend && npx vitest run` after each task. Vitest is configured (see
  `vite.config.ts` `test` block) with `include: ['tests/**/*.test.ts']` and
  `environment: 'node'`; DOM-dependent tests opt in per-file with
  `// @vitest-environment jsdom` (jsdom is installed). New test files therefore
  go under `frontend/tests/`, importing from `../../src/...`. This redesign
  must not modify `lib/*` logic or its tests.
- **Commit** at the end of each task with the message shown.

---

## File map

| File | Responsibility | Change |
|---|---|---|
| `frontend/src/theme/tokens.ts` | color tokens (light+dark) + font families | rewrite |
| `frontend/src/theme/tokens.css` | font `@import`, radii, shadows, texture | rewrite values |
| `frontend/src/theme/skin.css` | global skin (press/texture) | soften to flat |
| `frontend/src/ui/MtButton.vue` | button façade | terracotta filled CTA |
| `frontend/src/ui/MtMeeple.vue` | meeple glyph | **delete** |
| `frontend/src/components/CalendarDayCell.vue` | day cell encoding | rework |
| `frontend/src/views/CircleCalendarView.vue` | month layout + legend | rework |
| `frontend/src/views/CirclesView.vue` | circle hero cards | rework |
| `frontend/src/views/DayDetailView.vue` | host card + avatar row | restyle |
| `frontend/src/views/ProfileSettingsView.vue` | member-row look | restyle |
| `frontend/src/views/LoginView.vue` | hero/logo treatment | restyle |
| `frontend/src/components/*Dialog.vue` | settings/invite dialogs | restyle (token-driven) |
| `frontend/src/lib/circleStatus.ts` | next-viable-day per circle | **create** |
| `frontend/tests/lib/circleStatus.test.ts` | unit test (node env) | **create** |
| `frontend/src/composables/lastCircle.ts` | last-viewed-circle state | **create** |
| `frontend/tests/composables/lastCircle.test.ts` | unit test (jsdom env) | **create** |
| `frontend/src/components/AppNav.vue` | left rail + bottom nav | **create** |
| `frontend/src/App.vue` | mount AppNav + responsive shell | modify |
| `frontend/src/components/CalendarSideRail.vue` | desktop viable-days rail | **create** |

---

## Task 1: Color tokens + fonts (global re-skin)

**Files:**
- Modify: `frontend/src/theme/tokens.ts`
- Modify: `frontend/src/theme/tokens.css:10-11` (font `@import`)

- [ ] **Step 1: Swap the font import.** In `tokens.css` replace lines 10–11:

```css
/* Stitch identity: Noto Serif (display) + Plus Jakarta Sans (body). */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
```

- [ ] **Step 2: Update the `fonts` token** in `tokens.ts` (replace lines
  147–150):

```ts
export const fonts = {
  base: "'Plus Jakarta Sans', sans-serif",
  display: "'Noto Serif', Georgia, serif",
} as const
```

- [ ] **Step 3: Rewrite the `dark` color map** in `tokens.ts` with the Stitch
  Warmer Dark values. Replace the whole `dark` object (lines 96–144) with:

```ts
const dark: ThemeColors = {
  background: '#1a1614',
  'on-background': '#ede0dc',
  surface: '#1a1614',
  'on-surface': '#ede0dc',
  'surface-variant': '#433a35',
  'on-surface-variant': '#d0c4c1',
  'surface-container-lowest': '#120e0c',
  'surface-container-low': '#26211e',
  'surface-container': '#2e2824',
  'surface-container-high': '#39312c',
  'surface-container-highest': '#433a35',
  'surface-dim': '#1a1614',
  'surface-bright': '#4d423d',
  'surface-tint': '#f75f2d',
  outline: '#9c8e8b',
  'outline-variant': '#5a4139',
  // Terracotta is the filled CTA; peach is the accent/text tone.
  primary: '#f75f2d',
  'on-primary': '#3a0a00',
  'primary-container': '#7a2e16',
  'on-primary-container': '#ffdbd0',
  // Peach accent for icons/links/text on dark surfaces.
  'primary-accent': '#ffb59f',
  secondary: '#a3b18a',
  'on-secondary': '#1d2418',
  'secondary-container': '#3a4a2c',
  'on-secondary-container': '#d6e4c0',
  tertiary: '#ffb95f',
  'on-tertiary': '#472a00',
  'tertiary-container': '#653e00',
  'on-tertiary-container': '#ffddb8',
  // Domain tokens: attending=sage, hosting=terracotta, viable=amber.
  attend: '#a3b18a',
  'on-attend': '#1d2418',
  'attend-container': '#3a4a2c',
  'on-attend-container': '#d6e4c0',
  host: '#ffb59f',
  'on-host': '#5e1700',
  'host-container': '#7a2e16',
  'on-host-container': '#ffdbd0',
  viable: '#ffb95f',
  'on-viable': '#472a00',
  'viable-container': '#5a3d12',
  'on-viable-container': '#ffddb8',
  error: '#ffb4ab',
  'on-error': '#690005',
  'error-container': '#93000a',
  'on-error-container': '#ffdad6',
  'inverse-surface': '#ede0dc',
  'inverse-on-surface': '#2e2927',
  'inverse-primary': '#ae3100',
}
```

- [ ] **Step 4: Retune the `light` accents** to harmonise (keep parchment
  surfaces; shift `host` sky-blue → terracotta, `attend` leaf → sage). In the
  `light` object replace these keys only:

```ts
  primary: '#d8492f',
  'on-primary': '#ffffff',
  'primary-container': '#ffd9cf',
  'on-primary-container': '#5b1704',
  'primary-accent': '#d8492f',
  attend: '#6f8f5f',
  'on-attend': '#ffffff',
  'attend-container': '#dbe7c8',
  'on-attend-container': '#243218',
  host: '#c4502c',
  'on-host': '#ffffff',
  'host-container': '#ffd9cf',
  'on-host-container': '#5b1704',
```

- [ ] **Step 5: Verify build + both themes.** Run:

```
cd frontend && npm run build
```

Expected: build succeeds with no type errors. Then `npx vitest run` — expected:
all existing tests PASS (logic untouched).

- [ ] **Step 6: Visual smoke check.** Start the dev harness (see Conventions),
  open the app, confirm the dark theme renders warm-charcoal surfaces,
  terracotta buttons, serif headings. Toggle to light (system or theme switch)
  and confirm parchment surfaces + terracotta accents.

- [ ] **Step 7: Commit.**

```bash
git add frontend/src/theme/tokens.ts frontend/src/theme/tokens.css
git commit -m "Re-skin theme tokens and fonts to Stitch Warmer Dark"
```

---

## Task 2: Flatten the skin + terracotta filled CTA

The current skin is a chunky "wooden token" (3D lip, dotted board texture,
1.4rem radii). Stitch is flatter Material. Soften without removing the `Mt*`
press feedback entirely.

**Files:**
- Modify: `frontend/src/theme/tokens.css:13-36`
- Modify: `frontend/src/theme/skin.css`
- Modify: `frontend/src/ui/MtButton.vue`

- [ ] **Step 1: Retune non-color tokens** in `tokens.css` `:root` (replace the
  shape/elevation/motion/texture blocks):

```css
  /* Shape — softened, Stitch-style rounded surfaces */
  --mt-card-radius: 1rem;
  --mt-field-radius: 0.75rem;
  --mt-button-radius: 0.75rem;
  --mt-chip-radius: 999px;
  --mt-shell-width: 60rem;

  /* Elevation — quiet, warm shadows */
  --mt-shadow-card: 0 8px 24px -16px rgba(0, 0, 0, 0.55);
  --mt-shadow-raised: 0 14px 30px -18px rgba(0, 0, 0, 0.6);

  /* Minimal press lip (kept subtle, not a 3D token) */
  --mt-token-lip: 0.12rem;
  --mt-token-edge: rgba(0, 0, 0, 0.18);

  /* Motion */
  --mt-press-translate: 0.1rem;
  --mt-press-ms: 90ms;

  /* Texture — disabled (Stitch surfaces are flat) */
  --mt-board-dot: 0px;
  --mt-board-gap: 0rem;
```

- [ ] **Step 2: Remove the board texture** from `skin.css`. Open `skin.css`,
  find the rule that paints the dotted felt background (uses `--mt-board-dot` /
  `--mt-board-gap` via `radial-gradient` on `body`/app background) and replace
  the gradient with a flat `background: rgb(var(--v-theme-background))`. Keep
  everything else.

- [ ] **Step 3: Terracotta filled CTA in `MtButton.vue`.** The `solid` variant
  should render a flat terracotta fill (theme `primary` is now terracotta).
  Update the icon-button accent to use the peach accent. Replace `vColor`:

```ts
const vColor = computed(() => {
  if (props.tone === 'danger') return 'error'
  // Icon/ghost buttons read as light accents on dark surfaces.
  if (
    props.tone === 'primary' &&
    (props.variant === 'icon' || props.variant === 'ghost')
  ) {
    return 'primary-accent'
  }
  return props.tone
})
```

  Then ensure `primary-accent` resolves: it is defined in `tokens.ts` (Task 1),
  so Vuetify exposes it as a theme color.

- [ ] **Step 4: Verify.** `cd frontend && npm run build` (PASS), then visual
  check: cards are flatter with 1rem corners, no dotted texture; the primary
  "Create a Circle" button is a flat terracotta fill; app-bar icon buttons are
  peach.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/theme/tokens.css frontend/src/theme/skin.css frontend/src/ui/MtButton.vue
git commit -m "Flatten skin to Stitch style and add terracotta filled CTA"
```

---

## Task 3: Remove the meeple glyph

`MtMeeple` is the attending marker + brand mark in 7 files. Replace each with
mdi equivalents, then delete the component.

**Files (modify):** `App.vue`, `views/DayDetailView.vue`, `views/JoinView.vue`,
`views/LoginView.vue`, `views/CirclesView.vue`,
`views/CircleCalendarView.vue`, `components/CalendarDayCell.vue`.
**Files (delete):** `frontend/src/ui/MtMeeple.vue`.

- [ ] **Step 1: Brand mark (`App.vue`).** Replace the `<span class="brand__logo
  text-primary"><MtMeeple /></span>` with an mdi brand icon:

```html
<v-icon class="brand__logo text-primary" size="22">mdi-dice-5</v-icon>
```

  Remove the `MtMeeple` import.

- [ ] **Step 2: Attending marker (`CalendarDayCell.vue`).** Replace the meeple
  branch (lines ~34-39) so attending shows a sage dot/icon:

```html
<span
  v-else-if="myState === 'attending'"
  class="cell__mine cell__mine--attend"
>
  <v-icon size="15" color="attend">mdi-check-circle</v-icon>
</span>
```

  Remove the `MtMeeple` import and the `.cell__mine--meeple` style; add:

```css
.cell__mine--attend { margin-top: 2px; }
```

- [ ] **Step 3: Day-detail attendee (`DayDetailView.vue`).** Replace the
  `<span class="dd-meeple"><MtMeeple /></span>` prepend with:

```html
<v-icon color="attend" class="mr-3">mdi-check-circle</v-icon>
```

  Remove the `MtMeeple` import and the `.dd-meeple` style (Task 6 reworks this
  view further; this keeps it compiling in the meantime).

- [ ] **Step 4: Empty-state glyphs (`CirclesView.vue`, `JoinView.vue`,
  `LoginView.vue`).** Replace each `<MtMeeple />` used as a decorative glyph
  with `<v-icon size="64" color="primary-accent">mdi-dice-multiple</v-icon>`
  (scale per existing wrapper) and remove the `MtMeeple` imports. In
  `CircleCalendarView.vue` the legend uses `<MtMeeple />` inside the "Attending"
  chip — replace with `<v-icon start size="12" color="attend">mdi-check-circle</v-icon>`
  and remove the import + `.legend-meeple` style.

- [ ] **Step 5: Delete the component.**

```bash
rm frontend/src/ui/MtMeeple.vue
grep -rn "MtMeeple" frontend/src   # expect: no matches
```

- [ ] **Step 6: Verify.** `cd frontend && npm run build` (PASS) and
  `npx vitest run` (PASS).

- [ ] **Step 7: Commit.**

```bash
git add -A frontend/src
git commit -m "Replace meeple glyph with mdi icons and delete MtMeeple"
```

---

## Task 4: Calendar restyle

**Files:**
- Modify: `frontend/src/components/CalendarDayCell.vue`
- Modify: `frontend/src/views/CircleCalendarView.vue`

Preserve every state in `dayVisualState`; only the presentation changes.

- [ ] **Step 1: Month header (`CircleCalendarView.vue`).** Restyle `.cal-nav`
  to a Stitch-style header: large serif month label, left-aligned, with the
  chevrons grouped at the right. Replace `.cal-nav__label` CSS:

```css
.cal-nav { display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0 1rem; }
.cal-nav__label { flex: 1 1 auto; font-family: var(--v-font-family-display);
  font-size: 1.9rem; font-weight: 700; letter-spacing: -0.01em; }
```

  Keep the `MtButton` chevrons; move them after the label (label first) so the
  arrows sit on the right as in the Stitch mock.

- [ ] **Step 2: Day-cell visual encoding (`CalendarDayCell.vue`).** Apply the
  spec §5.1 encoding. Update the scoped styles:
  - `.cell` radius `0.6rem`, `gap: 2px` already on grid — round each cell:
    `border-radius: 0.6rem;`
  - Today: keep `.cell__date--today` but use terracotta `primary` fill with
    `on-primary` text (already terracotta from tokens).
  - Hosting ring: add a ring treatment when `myState === 'hosting'`:

```css
.cell--hosting { box-shadow: inset 0 0 0 2px rgb(var(--v-theme-host)); }
```

  Bind it in the template root `:class` with `'cell--hosting': myState === 'hosting'`.
  - Viable tint: `.cell--viable` already maps to `viable-container` (amber) —
    verify it reads as a warm amber tint.

- [ ] **Step 3: Legend chips (`CircleCalendarView.vue`).** Keep the chips; they
  now read from the new tokens (attend=sage, host=terracotta, viable=amber).
  No code change beyond Task 3's icon swap; confirm colors look right.

- [ ] **Step 4: Verify visually.** Screenshot the calendar (mobile + desktop),
  compare against `/tmp/stitch/m_calendar_dark.png` and
  `/tmp/stitch/d_calendar_dark.png`. Confirm: serif month header, rounded
  cells, today=terracotta circle, attending=sage check, hosting=terracotta
  ring, viable=amber tint, attendee count badge present, past dimmed.
  `npm run build` + `npx vitest run` PASS.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/components/CalendarDayCell.vue frontend/src/views/CircleCalendarView.vue
git commit -m "Restyle calendar to Stitch month layout and cell encoding"
```

---

## Task 5: Circle hero cards

Adds one pure function (next-viable-day per circle) with a real unit test, then
the card UI.

**Files:**
- Create: `frontend/src/lib/circleStatus.ts`
- Create: `frontend/tests/lib/circleStatus.test.ts`
- Modify: `frontend/src/views/CirclesView.vue`

- [ ] **Step 1: Write the failing test**
  (`frontend/tests/lib/circleStatus.test.ts`):

```ts
import { describe, it, expect } from 'vitest'
import { nextViableDate } from '../../src/lib/circleStatus'
import type { DayViability } from '../../src/types'

const v = (date: string, is_viable: boolean): DayViability =>
  ({ date, is_viable } as DayViability)

describe('nextViableDate', () => {
  it('returns the earliest viable date on or after today', () => {
    const map = {
      '2026-06-10': v('2026-06-10', true),
      '2026-06-20': v('2026-06-20', true),
      '2026-06-25': v('2026-06-25', false),
    }
    expect(nextViableDate(map, '2026-06-14')).toBe('2026-06-20')
  })

  it('returns null when no upcoming day is viable', () => {
    const map = { '2026-06-10': v('2026-06-10', true) }
    expect(nextViableDate(map, '2026-06-14')).toBeNull()
  })
})
```

- [ ] **Step 2: Run it — expect FAIL.**

```
cd frontend && npx vitest run tests/lib/circleStatus.test.ts
```

Expected: FAIL — `nextViableDate` is not defined.

- [ ] **Step 3: Implement** (`circleStatus.ts`):

```ts
import type { DayViability } from '../types'

/**
 * Earliest viable date on or after `todayStr` (ISO yyyy-MM-dd), or null.
 * Pure: operates on the viability map already loaded by the circles
 * composable. No network.
 */
export function nextViableDate(
  viability: Record<string, DayViability>,
  todayStr: string,
): string | null {
  const upcoming = Object.values(viability)
    .filter((d) => d.is_viable && d.date >= todayStr)
    .map((d) => d.date)
    .sort()
  return upcoming[0] ?? null
}
```

- [ ] **Step 4: Run it — expect PASS.**

```
cd frontend && npx vitest run tests/lib/circleStatus.test.ts
```

Expected: PASS (2 tests).

- [ ] **Step 5: Rework `CirclesView.vue` to hero cards.** Replace the
  `.mt-tile` card body with a hero-image card. Key structure (inside the
  `v-for`):

```html
<MtCard interactive :to="`/circles/${circle.id}`" class="circle-card">
  <div class="circle-card__hero" :style="heroStyle(circle)">
    <span v-if="!circle.image_ref" class="circle-card__initials">
      {{ initials(circle.name) }}
    </span>
  </div>
  <div class="circle-card__body">
    <div class="circle-card__name">{{ circle.name }}</div>
    <div class="circle-card__desc text-medium-emphasis">
      {{ circle.description || 'No description yet' }}
    </div>
    <div class="circle-card__next text-medium-emphasis">
      <v-icon size="14" start>mdi-calendar-check</v-icon>
      {{ nextLabel(circle.id) }}
    </div>
  </div>
</MtCard>
```

  Script additions:

```ts
import { nextViableDate } from '../lib/circleStatus'
import { safeFormat } from '../lib/datetime'
// heroStyle: image banner or warm gradient fallback
function heroStyle(c: { image_ref: string | null }) {
  return c.image_ref
    ? { backgroundImage: `url(${c.image_ref})` }
    : {
        background:
          'linear-gradient(135deg, rgb(var(--v-theme-primary)),' +
          ' rgb(var(--v-theme-tertiary)))',
      }
}
function initials(name: string): string {
  return name.trim().slice(0, 2).toUpperCase()
}
function nextLabel(circleId: string): string {
  // viability for the circle list is not preloaded per-circle in v1;
  // show a neutral label until a circle is opened. If the circles
  // composable exposes per-circle viability, use nextViableDate here.
  return 'Open to see upcoming days'
}
```

  > Note: the circles list endpoint does not currently return per-circle
  > viability. `nextViableDate` is wired and unit-tested so that, if/when the
  > list payload includes a viability map, `nextLabel` becomes
  > `const d = nextViableDate(map, todayStr); return d ? 'Next: ' +
  > safeFormat(d, 'EEE, MMM d') : 'No upcoming viable days'`. Do **not** add a
  > new backend call in this redesign.

  Add scoped styles for `.circle-card__hero` (height ~120px, `background-size:
  cover`, `background-position: center`, rounded top), `.circle-card__initials`
  (centered serif, large, on a translucent scrim), `.circle-card__body`
  (padding 0.9rem 1rem), `.circle-card__name` (serif, 1.2rem),
  `.circle-card__next` (0.8rem, top margin).

- [ ] **Step 6: Verify visually.** Screenshot `/circles` (mobile + desktop) vs
  `/tmp/stitch/m_list_dark.png` and `/tmp/stitch/d_list.png`. Confirm hero
  banners (with gradient+initials fallback when `image_ref` null), serif names,
  next-day line, Create button. `npm run build` + `npx vitest run` PASS.

- [ ] **Step 7: Commit.**

```bash
git add frontend/src/lib/circleStatus.ts frontend/tests/lib/circleStatus.test.ts frontend/src/views/CirclesView.vue
git commit -m "Add circle hero cards with image fallback and next-day helper"
```

---

## Task 6: Day detail restyle

**Files:**
- Modify: `frontend/src/views/DayDetailView.vue`

- [ ] **Step 1: Host card + attendee avatar row.** Above the attendee list, add
  a highlighted host card and an avatar row. Replace the Attendees `<v-list>`
  block with:

```html
<div v-if="hostAttendee" class="dd-host">
  <v-avatar size="40" color="host">
    <span class="text-caption font-weight-bold">
      {{ initials(hostAttendee.pseudonym) }}
    </span>
  </v-avatar>
  <div>
    <div class="text-caption text-medium-emphasis">Host</div>
    <div class="dd-host__name">{{ hostAttendee.pseudonym }}</div>
  </div>
  <v-icon color="host" class="ml-auto">mdi-home-variant</v-icon>
</div>

<div class="dd-attendees">
  <div class="text-subtitle-2 mb-2">
    Attending ({{ enrichedAttendees.length }})
  </div>
  <div class="dd-avatars">
    <v-avatar
      v-for="a in enrichedAttendees"
      :key="a.user_id"
      size="36"
      :color="a.state === 'hosting' ? 'host' : 'attend'"
    >
      <span class="text-caption font-weight-bold">
        {{ initials(a.pseudonym) }}
      </span>
    </v-avatar>
  </div>
</div>
```

  Script additions:

```ts
const hostAttendee = computed(
  () => enrichedAttendees.value.find((a) => a.state === 'hosting') ?? null,
)
function initials(name: string): string {
  return (name?.trim().slice(0, 2) || '?').toUpperCase()
}
```

  Scoped styles: `.dd-host` (flex, gap, padding, `surface-container`
  background, rounded), `.dd-host__name` (serif, 1.05rem), `.dd-avatars` (flex,
  wrap, gap 0.4rem).

- [ ] **Step 2: Notes block** stays as-is (kept, contract §10). Confirm the
  textarea + "Add Note" button read correctly with the new tokens. No "RSVP"
  button is added.

- [ ] **Step 3: Verify visually.** Screenshot `/circles/:id/day/:date` vs
  `/tmp/stitch/m_daydetail.png`. Confirm host card, attendee avatars (sage for
  attending, terracotta for hosting), notes list + composer. `npm run build` +
  `npx vitest run` PASS.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/views/DayDetailView.vue
git commit -m "Restyle day detail with host card and attendee avatars"
```

---

## Task 7: Settings, members & login restyle

**Files:**
- Modify: `frontend/src/views/ProfileSettingsView.vue`
- Modify: `frontend/src/views/LoginView.vue`
- (Dialogs `CreateCircleDialog.vue`, `InviteDialog.vue`,
  `ConstraintEditorDialog.vue`, `CircleNotificationsDialog.vue` inherit the
  token/skin changes; only touch them if a hardcoded color/radius fights the
  new theme.)

- [ ] **Step 1: Member-row treatment.** In `ProfileSettingsView.vue`, wherever
  members/identities are listed, render each as a Stitch member row: leading
  `v-avatar` with initials (`color="surface-container-high"`), name in body
  weight, a role chip (`<v-chip size="x-small" color="primary" variant="tonal">`)
  and a muted "Joined <date>" subtitle using `safeFormat(joined_at, 'MMM yyyy')`.
  If the view does not currently list members, restyle the existing settings
  cards to the flat Stitch card look only.

- [ ] **Step 2: Login hero (`LoginView.vue`).** Restyle to the Stitch sign-in
  hero: centered brand icon (`mdi-dice-5`, peach), serif "Welcome to
  MeepleTime" headline, a "Gather your party" subline, then the **existing**
  sign-in action(s) — the Keycloak redirect button and (under `VITE_DEV_AUTH`)
  the dev-login picker. **Do not** add email/password or social buttons.

- [ ] **Step 3: Verify visually.** Screenshot `/login` vs
  `/tmp/stitch/m_signin_dark.png` (hero only — no form) and the profile/members
  screen vs `/tmp/stitch/m_settings.png`. `npm run build` + `npx vitest run`
  PASS.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/views/ProfileSettingsView.vue frontend/src/views/LoginView.vue
git commit -m "Restyle login hero and member rows to Stitch look"
```

---

## Task 8: Desktop two-pane shell

Adds the last-viewed-circle composable (unit-tested), a nav component (left
rail on desktop, bottom nav on mobile), and the calendar right rail.

**Files:**
- Create: `frontend/src/composables/lastCircle.ts`
- Create: `frontend/tests/composables/lastCircle.test.ts`
- Create: `frontend/src/components/AppNav.vue`
- Create: `frontend/src/components/CalendarSideRail.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/CircleCalendarView.vue` (mount the rail at ≥md)

- [ ] **Step 1: Failing test for last-viewed circle**
  (`frontend/tests/composables/lastCircle.test.ts`). The first line's
  `@vitest-environment jsdom` pragma is **required** — the test uses
  `localStorage`, which the default node env lacks:

```ts
// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { rememberCircle, lastCircleId } from '../../src/composables/lastCircle'

beforeEach(() => localStorage.clear())

describe('lastCircle', () => {
  it('remembers and reads back the last circle id', () => {
    expect(lastCircleId()).toBeNull()
    rememberCircle('abc')
    expect(lastCircleId()).toBe('abc')
  })
})
```

- [ ] **Step 2: Run — expect FAIL.**

```
cd frontend && npx vitest run tests/composables/lastCircle.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement** (`lastCircle.ts`):

```ts
const KEY = 'mt:last-circle'

/** Persist the most recently opened circle id. */
export function rememberCircle(id: string): void {
  try {
    localStorage.setItem(KEY, id)
  } catch {
    /* storage unavailable — nav just falls back to the list */
  }
}

/** The last opened circle id, or null. */
export function lastCircleId(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}
```

- [ ] **Step 4: Run — expect PASS.**

```
cd frontend && npx vitest run tests/composables/lastCircle.test.ts
```

Expected: PASS.

- [ ] **Step 5: Record the circle on open.** In `CircleView.vue` `onMounted`,
  call `rememberCircle(circleId)` (import from `../composables/lastCircle`).

- [ ] **Step 6: `AppNav.vue`.** A responsive nav with three destinations
  (Circles → `/circles`, Calendar → last circle or `/circles`, Profile →
  `/profile`). Use `useDisplay()` from Vuetify: render a
  `v-navigation-drawer rail permanent` at `mdAndUp`, and a bottom
  `v-bottom-navigation` below `md`. Calendar target:

```ts
import { useRouter } from 'vue-router'
import { lastCircleId } from '../composables/lastCircle'
function goCalendar() {
  const id = lastCircleId()
  router.push(id ? `/circles/${id}` : '/circles')
}
```

  Items use mdi icons: `mdi-account-group` (Circles), `mdi-calendar-month`
  (Calendar), `mdi-account-circle` (Profile). Hide AppNav when
  `!auth.isLoggedIn.value` or on `/login` and `/auth/callback`.

- [ ] **Step 7: Mount in `App.vue`.** Add `<AppNav v-if="auth.isLoggedIn.value" />`
  inside `<v-app>` (before `<v-main>`). The rail/bottom-nav reserve their own
  space via Vuetify layout. Keep the existing `v-app-bar`.

- [ ] **Step 8: `CalendarSideRail.vue`.** A list of upcoming viable days for the
  current circle, reusing `buildUpcomingDays(viability, todayStr, true)`. Props:
  `circleId`. It reads `useCircles().viability`. Render each day as a compact
  row (serif date + attendee count chip) linking to the day detail. This is the
  same data `CircleListView` already shows — extract the row markup into the
  rail; do not add a network call (the calendar view already fetches viability).

- [ ] **Step 9: Show the rail at ≥md** in `CircleCalendarView.vue`. Wrap the
  calendar container and the rail in a flex row; render
  `<CalendarSideRail :circle-id="circleId" />` only `v-if="mdAndUp"`
  (`useDisplay()`), width ~320px, on the right.

- [ ] **Step 10: Verify visually.** At 1280px: left rail + calendar + right
  viable-days rail (compare `/tmp/stitch/d_calendar_dark.png`, minus the
  out-of-scope invitations/matchmaking). At 390px: bottom nav with three items,
  Calendar tab routes to the last opened circle. `npm run build` +
  `npx vitest run` PASS (incl. the new lastCircle test).

- [ ] **Step 11: Commit.**

```bash
git add frontend/src/composables/lastCircle.ts frontend/tests/composables/lastCircle.test.ts frontend/src/components/AppNav.vue frontend/src/components/CalendarSideRail.vue frontend/src/App.vue frontend/src/views/CircleView.vue frontend/src/views/CircleCalendarView.vue
git commit -m "Add responsive desktop shell with nav rail and calendar side rail"
```

---

## Task 9: Final verification sweep

**Files:** none (verification only).

- [ ] **Step 1: Full test + build.**

```
cd frontend && npx vitest run && npm run build
```

Expected: all tests PASS, build clean.

- [ ] **Step 2: Lint/format.**

```
pre-commit run --all-files
```

Expected: prettier passes (or auto-formats; re-commit if it edits files).

- [ ] **Step 3: Visual regression sweep** via Playwright dev-login at 390px and
  1280px for: login, circles list, calendar, day detail, profile/settings.
  Compare each against its `/tmp/stitch/*.png`. Confirm no meeple glyph remains
  and both light/dark themes are coherent.

- [ ] **Step 4: Confirm scope.** `git diff master --stat` shows only
  `frontend/src/**`, the two new tests under `frontend/tests/`, and the docs
  specs/plans — **no** `backend/`, no edits to the existing `frontend/tests/lib/*`
  suite or any `src/lib/*` logic, no `router/index.ts` route changes
  (behavior), no auth files.

- [ ] **Step 5: Final commit (if formatting changed anything).**

```bash
git add -A && git commit -m "Format and finalize Stitch redesign"
```

---

## Self-review notes

- **Spec coverage:** tokens/fonts (T1), flat skin + terracotta CTA (T2), meeple
  removal (T3), calendar (T4), circle cards (T5), day detail (T6),
  settings/members + login (T7), desktop shell + last-viewed-circle (T8),
  rejects are honored by omission and called out in T7 (no social/email login)
  and T6 (no RSVP). Light theme retuned in T1.
- **Known constraint surfaced, not hidden:** the circles-list payload has no
  per-circle viability, so `nextLabel` shows a neutral string; `nextViableDate`
  is built + tested for when that data exists, with no new backend call (honors
  "presentation-only").
- **Types:** `nextViableDate(Record<string, DayViability>, string)`,
  `rememberCircle(string)`, `lastCircleId(): string|null`,
  `hostAttendee`/`initials` used consistently across tasks.
