# Stitch-aligned Frontend Redesign — Design

**Date:** 2026-06-14
**Status:** Approved (pending spec review)
**Scope:** Frontend visual redesign only. No backend, API, domain-logic,
auth, or contract changes. All of `lib/*`, composables, `api/*`, and the
backend are untouched.

## 1. Goal

Bring the local MeepleTime SPA up to the visual quality of the "MeepleTime"
Stitch project by adopting its **Warmer Dark** identity and its stronger
layouts (mobile calendar, circle cards, day detail, settings) and adding a
desktop two-pane shell — **without** importing any of the out-of-scope
product features the Stitch project drifted into (it became a board-game-café
/ social app).

This is a presentation-layer change. The token architecture
(`theme/tokens.ts` is the single source of truth) and the `Mt*` component
layer are reused, not rebuilt.

## 2. Decisions (locked)

| Decision | Choice |
|---|---|
| Scope | Mobile screens **+** desktop two-pane shell |
| Theme | Adopt the Stitch *Warmer Dark* look fully |
| Light theme | Keep it — restyle into a warm-parchment companion (system light/dark still switches) |
| Brand motif | Drop the bespoke meeple glyph (`MtMeeple`); use standard iconography + imagery |
| Icon set | **Keep mdi** (Vuetify-native). Do **not** switch to Material Symbols — only the meeple glyph is removed |
| Desktop "Calendar" nav | Routes to the **last-viewed circle** (falls back to the Circles list if none) |
| Build approach | Token-swap + in-place restyle, with deeper structural rework only on the calendar and circle cards |

## 3. Source identity (extracted from Stitch "Warmer Dark" HTML)

**Fonts:** Noto Serif (display/headlines, 700/800) + Plus Jakarta Sans
(body, 400–700). Loaded via `@fontsource`. Replaces Fredoka/Nunito.

**Dark palette (canonical):**

| Role | Hex |
|---|---|
| background / surface | `#1a1614` |
| surface-container-low | `#26211e` |
| surface-container | `#2e2824` |
| surface-container-high | `#39312c` |
| surface-container-highest / surface-variant | `#433a35` |
| surface-bright | `#4d423d` |
| outline | `#9c8e8b` · outline-variant `#5a4139` |
| on-surface | `#ede0dc` · on-surface-variant `#d0c4c1` |
| primary (accent/peach) | `#ffb59f` |
| primary-container (filled terracotta CTA) | `#f75f2d` |
| secondary (sage) | `#a3b18a` |
| tertiary (amber) | `#ffb95f` · tertiary-container `#ca8100` |
| error | `#ffb4ab` |

**CTA nuance:** Stitch's prominent filled buttons/FAB use the **terracotta**
`#f75f2d` (the `primary-container` tone), while peach `#ffb59f` is the accent
for icons/links/text on dark. The `Mt*` button "primary filled" tone must map
to terracotta, not peach, to match Stitch. Captured here so the `Mt*` tone
mapping is set deliberately rather than defaulting to Vuetify's `primary` bg.

## 4. Token & domain-color mapping

`theme/tokens.ts` keeps its semantic domain tokens (`attend`, `host`,
`viable`, plus `*-container` pairs) but remaps the hues:

| Domain token | New meaning | Dark | Light (parchment companion) |
|---|---|---|---|
| `primary` | terracotta/peach | peach `#ffb59f`, filled `#f75f2d` | terracotta `#d8492f` (≈ current coral) |
| `attend` (attending) | **sage green** (was leaf) | `#a3b18a` | retuned sage |
| `host` (hosting) | **terracotta** (was sky-blue) | `#f75f2d`/`#ffb59f` family | terracotta |
| `viable` | **amber** (honey) | `#ffb95f` | honey (unchanged) |
| `tertiary` | amber/warning | `#ffb95f` | clay/amber |

- Light theme keeps its parchment **surfaces**; only the accents retune
  (`host` sky-blue → terracotta, `attend` leaf → sage) so both themes read as
  one family.
- `host` and `primary` share the terracotta family. They never collide
  visually because hosting is always drawn as a **ring + icon**, never a
  fill, while filled primary surfaces (buttons, today marker) use solid
  terracotta. (See §5.1.)

## 5. Screen specs

### 5.1 Calendar — `CircleCalendarView.vue` + `CalendarDayCell.vue` (hybrid rework)

Adopt the Stitch month layout; **preserve all existing domain states** (Stitch
shows only 3; the app has more, and none are dropped).

Layout:
- Large **serif month header** + subtitle line, prev/next chevrons (prev still
  disabled before the current month), rounded month container, roomier cells.
- Legend + helper text restyled as Stitch chips; copy preserved
  ("Tap a day to set availability · long-press/right-click for options").

Day-cell encoding (all retained from current `dayVisualState`):
- **Today** → date number in a filled terracotta circle.
- **Own state** → attending = sage fill/dot; hosting = terracotta **ring** +
  `mdi-home-variant`.
- **Aggregate** → viable = amber surface tint; over-soft-max = amber warning
  border; multiple-hosts = small sage dot; attendee count = numeric badge
  (kept, bottom-right).
- **Past** → dimmed; **dimmed (viable-only filter)** → faded + non-interactive.

Interaction is unchanged: tap cycles (empty→attending→hosting→empty);
long-press/right-click opens `DayContextSheet`. `DayContextSheet`,
`ConstraintEditorDialog`, `InviteDialog`, `CircleNotificationsDialog` are
restyled by the token swap only.

### 5.2 Circle cards — `CirclesView.vue` (hybrid rework)

Replace meeple-avatar tiles with Stitch **hero-image cards**:
- `circle.image_ref` as banner image.
- Circle name in serif; description as secondary line.
- A "Next: <next viable/upcoming day>" line, derived from existing viability
  data (the same source `CircleListView`/`buildUpcomingDays` already uses). No
  new backend.
- Status chip (e.g. "Active" when an upcoming viable day exists).
- **Fallback** when `image_ref` is null: warm gradient banner + circle initials.
- Keep the full-width "Create a Circle" action and the Join-by-PIN dialog
  (`MtPinField`).

### 5.3 Day detail — `DayDetailView.vue` (restyle)

Re-skin to Stitch's structure:
- Highlighted **host card** at top (host pseudonym + role).
- **Attendee avatar row**: initials-based `VAvatar` (membership model stores
  pseudonyms, not photos), with overflow "+N".
- Notes list + composer **kept** (contract §10, append-only).
- **Dropped:** "Update RSVP" button and "Bringing…" — the app's model is
  tap-to-cycle availability on the calendar, not yes/no RSVP. This view stays
  an inspect + notes surface. Remains a route (mobile and desktop).

### 5.4 Settings & members (restyle where present)

Stitch's "Circle Settings" (name field + member list with role badge + joined
date + Leave Circle) is the target look. Today the app has **no dedicated
circle-settings screen** — this lives in dialogs, and `ProfileSettingsView` is
the *user* profile.

- Restyle the existing member/settings **dialogs** and `ProfileSettingsView`
  to the Stitch member-row treatment (avatar initials, role chip, joined date).
- A dedicated circle-settings *screen* is **out of scope** for this redesign
  (it would be a feature addition); noted as a possible follow-up.

### 5.5 Auth — `LoginView.vue` (restyle only)

Re-skin to the Stitch sign-in's warm hero/logo treatment **only**. The
email/password form and Google/Apple buttons are **rejected** — they violate
the OIDC-only contract (§1a). The dev-login picker stays as-is functionally.

## 6. Desktop shell (new responsive layout)

A breakpoint-aware shell wrapping the existing routes:

- **≥ md:** slim **left icon rail** — Circles · Calendar · Profile — + main
  content. On the calendar, a **right rail** renders the viable/upcoming-days
  list (reusing `buildUpcomingDays`; real data, no new endpoint). This rail
  replaces the Stitch desktop rail's out-of-scope content (invitations,
  matchmaking).
- **< md:** keep the current top app bar; add Stitch's **bottom nav**
  (Circles · Calendar · Profile).
- **"Calendar" nav target:** the last-viewed circle, tracked in a small piece
  of shared state (composable/localStorage); falls back to `/circles` when no
  circle has been visited.

The Calendar/List tab strip inside `CircleView` is retained (restyled).

## 7. Out of scope — explicit rejects (no work)

Grounded in `contract.md`; do not implement:
- Email/password or Google/Apple login (§1a OIDC-only).
- Gamification: achievements, badges, "Meeple Master", game library, wishlist.
- Maps / address, and "Sync to Calendar" Google/Apple (§19 calendar sync).
- In-app invitation inbox, Accept/Decline, "spots left", matchmaking /
  "high match" / wishlist matching.
- RSVP yes/no, "Bringing…" snacks/games, discussion chat threads.

Day **notes** remain the only append-only text surface (contract §10).

## 8. Execution approach

Incremental, presentation-only:

1. **Tokens + fonts** (`theme/tokens.ts`, `@fontsource`, `Mt*` tone mapping
   incl. terracotta filled CTA). Re-skins the whole app in one step; verify
   both themes render.
2. **Calendar** (cell encoding + month layout).
3. **Circle cards.**
4. **Day detail.**
5. **Desktop shell** (rail nav + right rail + last-viewed-circle state +
   mobile bottom nav).
6. **Settings/members + login** restyle.
7. Remove `MtMeeple` usages; delete the component once unreferenced.

Domain logic, routes' behavior, and API stay unchanged throughout. Each step
is independently viewable.

## 9. Testing / verification

- This is visual; rely on manual verification via the Playwright dev-login
  bypass (`DEV_AUTH_ENABLED` / `VITE_DEV_AUTH`) to drive the SPA and screenshot
  each redesigned screen at mobile and desktop widths, comparing against the
  Stitch reference.
- Existing unit tests for `lib/*` (calendar, viability, members) must continue
  to pass unchanged — they are logic, not presentation, and this redesign must
  not touch them.
- Lint/format via pre-commit (prettier) on all changed frontend files;
  80-char limit applies.
