# Meeting Availability App v1 Implementation Contract

## 1. Purpose

Build a small, mobile-first web application for private circles of friends to
discover viable meetup days with minimal clerical overhead.

The core interaction is per-day availability marking inside a circle. A day
becomes an emergent meetup candidate when at least one member marks positive
availability for that day.

The application is invite-only. It supports self-hosting and should be simple to
operate.

## 1a. Authentication strategy

Authentication is handled exclusively via **Keycloak** (self-hosted
OIDC provider), Option A of the OIDC module.

- The Vue frontend is a public OIDC client. It performs the
  authorization code + PKCE flow and holds tokens in the browser.
  There is no in-app login form.
- The FastAPI backend is a stateless resource server. It validates
  bearer tokens on every request using Keycloak's JWKS endpoint.
  It never participates in the OIDC flow.
- `client_secret` must never appear in frontend code or build
  artefacts.
- Local password authentication is explicitly out of scope and
  must not be re-introduced.
- GitHub and Twitter login are out of scope for v1. Social
  providers may be configured inside Keycloak at a later date
  without changes to application code.
- Keycloak provider configuration (realm, client, redirect URIs)
  is documented in `docs/operator/keycloak.md`.

## 2. Chosen stack

Use these technologies for v1:

- Backend: FastAPI (Python)
- Database: PostgreSQL
- Frontend: Vue 3 with TypeScript
- UI framework: Vuetify
- Identity provider: Keycloak (self-hosted OIDC)
- Containerization: Docker and docker-compose or Docker stack
  compatible setup

Rationale:
- These choices align with existing operator experience.
- They are mature and sufficient for the expected scale.
- No strong argument exists to deviate for v1.
- Keycloak adds operational surface but provides a proven,
  auditable identity layer that removes password handling from
  the application entirely. This trade-off is explicitly
  accepted.

## 3. Product terminology

Use these terms consistently in code and documentation.

### 3.1 Circle
User-facing replacement for “group”.

A circle is a private set of members who share a calendar-like view of days and
can mark availability.

### 3.2 Member
A user inside a specific circle.

A member has a per-circle pseudonym and circle-specific capabilities.

### 3.3 Day
A calendar date in the circle timezone.

A day is represented logically as a local date and semantically as a time range
from local midnight inclusive to next local midnight exclusive.

### 3.4 Availability
A member’s state for a specific circle-day.

Allowed states:
- empty
- attending
- hosting

For v1, `empty` means unavailable. There is no distinction between “unknown” and
“explicit no”.

### 3.5 Emergent meetup
A derived concept. A day is considered an emergent meetup candidate when at
least one member has a non-empty availability on that day.

This is mainly presentation logic. It may also have lightweight persisted
metadata via auxiliary tables.

### 3.6 Day overrides
Optional per-day persisted data that overrides circle defaults for one day.

### 3.7 Day note
Optional lightweight note or comment thread attached to one circle-day.

## 4. Product scope for v1

## Included

- Invite-only circles
- Authentication required before joining a circle
- Per-circle pseudonyms
- Mobile-first day calendar UI
- Tap-to-cycle availability interaction
- Circle timezone
- Circle-level defaults
- Optional per-host day constraints
- Derived viability markers
- “Display only viable days” toggle
- Day detail view
- Optional day notes/comments
- Notifications on meaningful derived transitions
- Past day archive behavior

## Excluded

- Anonymous access
- Calendar provider sync
- Public circles or discovery
- Rich event finalization workflow
- Explicit host assignment workflow
- Ranking days by score
- Required attendees
- Backup host vs primary host distinction
- Complex moderation features
- Complex past-event logic
- Realtime collaboration as a hard requirement

## 5. Core UX contract

## 5.1 Primary interaction
The default mobile interaction is direct day tapping.

Each tap on a day owned by the signed-in member cycles that member’s
availability state for that circle-day:

`empty -> attending -> hosting -> empty`

Requirements:
- State updates must feel immediate in the UI.
- Undo must be easy by continuing the cycle.
- No confirmation modal for the basic cycle.
- No separate “cancel session” action exists.

## 5.2 Day detail interaction
A separate day detail view must exist to inspect aggregate state for a day.

The exact gesture or entry pattern is left open for later refinement, but v1
must provide some way to access day details without blocking the primary
tap-cycle flow.

## 5.3 Calendar horizon
Users can browse:
- past archived days
- today
- any future days

The default landing view should emphasize current and near-future days.

## 5.4 Sort and presentation
Days are always presented chronologically. No score-based ranking is allowed in
v1.

A toggle may filter the visible list or calendar to viable days only.

## 6. Circle settings for v1

Each circle must support the following persisted settings:

- name
- description
- image reference
- timezone
- invite token or invite-link mechanism
- host_needed: boolean
- minimum_attendees: nullable integer
- soft_max_attendees: nullable integer
- hard_max_attendees: nullable integer
- external_links: structured list or JSON payload for links such as WhatsApp,
  Discord, Slack
- created_by_user_id
- created_at
- updated_at

Behavioral notes:
- `host_needed` controls whether hosting availability is required for a day to be viable.
- If `soft_max_attendees` is exceeded, the day remains viable but is visually marked.
- If `hard_max_attendees` is exceeded, the day is non-viable and visibly marked.
- `minimum_attendees` is a hard lower bound for viability if set.

## 7. Membership model

A membership links a user to a circle.

Persist at least:
- circle_id
- user_id
- pseudonym
- role
- can_host_default: boolean
- joined_at
- notification_preferences

Constraints:
- pseudonym is freely chosen per circle
- pseudonym must be unique within a circle for v1
- role values for v1 should be minimal: owner, admin, member
- `can_host_default` indicates that this member is generally able to host, but actual hosting viability for a day still depends on that member selecting the `hosting` availability state for the day

## 8. Availability model

Persist one row per `(circle_id, user_id, local_date)` when the state is non-empty.

Recommended representation:
- circle_id
- user_id
- local_date
- state enum: attending, hosting
- created_at
- updated_at

Rules:
- Do not persist rows for `empty`.
- Deleting an availability row is equivalent to setting the state to `empty`.
- `local_date` is interpreted in the circle timezone.
- Past dates should be treated as read-only for normal users in v1.

## 9. Host day constraints model

Host day constraints capture situational capacity limits for a specific
hosting member on a specific date — for example, reduced space due to
renovations, or a reduced comfortable maximum number of guests.  They
are personal to the hosting member and supplemental to circle defaults.

Persist one row per `(circle_id, user_id, local_date)` when constraints
are set.

Allowed constraint fields in v1:
- override_minimum_attendees: nullable integer
- override_soft_max_attendees: nullable integer
- override_hard_max_attendees: nullable integer

Note: `host_needed` is a circle-level policy and is not overridable
per-host.  There is no `override_host_needed` field.

Merge rule: when a member's constraint and the circle default both
provide a value for the same field, the more restrictive value applies:
- minimum threshold → take the maximum of the two values
- maximum threshold → take the minimum of the two values

Rules:
- Constraints are optional.
- Absence of a row means circle defaults apply for that member's hosting
  eligibility calculation.
- A day only counts as an emergent meetup candidate if at least one
  member has non-empty availability on that day.
- Constraint records alone must not create a meetup candidate.

Permissions:
- Any circle member may create, update, or delete their own constraints.
- Circle owner or admin may manage any member's constraints (for cases
  where a host is unavailable to update their own record).

## 10. Day notes/comments

Support lightweight notes attached to a circle-day.

Minimum v1 requirement:
- plain text note or simple comment entries
- stored separately from availability rows
- associated with `(circle_id, local_date)`

Rules:
- Notes are optional.
- Notes must be viewable from the day detail view.
- Notes themselves remain plain text; rich text is not required for
  the notes feature.
- Rich-text editing (Quill) is now permitted, but only for the
  separate day-description feature (see section 10.1), not for notes.

Permissions:
- Any circle member may add a note/comment in v1 unless later policy says otherwise.
- Edit/delete policy is left as an open question unless needed for the initial implementation. Prefer a simple append-only model if uncertain.

## 10.1 Day description

A *description* is static session detail attached to a circle-day,
distinct from the threaded notes of section 10 (singular, not a
conversation: no replies). It captures details for a single session
— for example a hiking group's trail or meetup location — and is
folded into the viability email once the day becomes viable.

Shape (depends on whether the circle requires a host):
- Circles where a host is **not** required (`host_needed = false`):
  a single circle-wide description per `(circle_id, local_date)`.
- Circles that **require** a host (`host_needed = true`): one
  description **per host** for the day (a host is a member whose
  availability state is `hosting`), so members can compare offers
  when several hosts volunteer.

Rules:
- Descriptions are optional and viewable from the day detail view.
- The canonical stored representation is a Quill **Delta** document
  (JSON). HTML is only ever derived at render time and is sanitised
  on the client (DOMPurify) before display; it is never stored.
- The viability email includes a plain-text rendering of the
  description(s) for a day that became viable.

Permissions:
- Circle-wide description: only the circle **owner or admin** may
  set, edit, or clear it.
- Per-host description: owned and editable by **that host**; the
  circle **owner or admin** may also manage any host's description.

## 11. Viability rules

Viability is derived from current state. There is no explicit finalization flow in v1.

For a given circle-day, compute:

- attendee_count = number of members with state in {attending, hosting}
- hosting_count = number of members with state = hosting

### 11.1 Evaluation paths

**No hosting members present**

Evaluate the day against circle defaults directly:
- if `circle.host_needed` is true, the day is non-viable
- if `circle.minimum_attendees` is set,
  `attendee_count >= minimum_attendees` must hold
- if `circle.hard_max_attendees` is set,
  `attendee_count <= hard_max_attendees` must hold

**Hosting members present**

For each hosting member, resolve their effective constraints by merging
`circle` defaults with their personal `host_day_constraint` record (if
any), taking the more restrictive value per field (see section 9).
A hosting member is a *viable host* for the day if:
- `attendee_count >= effective_minimum_attendees` (if set)
- `attendee_count <= effective_hard_max_attendees` (if set)

The day is viable when `viable_host_count >= 1` (any-host logic).

### 11.2 Warning markers

A day is still viable but should show a soft-max warning if any viable
host has their effective soft_max exceeded by the current attendee count.

When `viable_host_count > 1`, the frontend should display an
informational marker indicating that multiple hosts are available and
members should agree out-of-band on who hosts.  There is no explicit
host designation workflow in v1.

### 11.3 Empty days
A day with zero non-empty availabilities is not a meetup candidate and is not viable.

## 12. Notification contract

Notifications must be based on derived state transitions, not raw tap events.

### 12.1 Debounce requirements

Use a coarse debounce per `circle_id` measured in seconds, not milliseconds. The debounce accumulates every changed day for the circle and emits a single aggregated summary, rather than one notification per changed day.

Required behavior:
- Save availability changes immediately.
- Reflect state changes immediately in the acting user’s UI.
- Delay derived notification evaluation for a sliding debounce window that resets on each change anywhere in the circle.
- Collapse repeated changes — across multiple days of the same circle — within the window into one evaluation and one aggregated summary notification.
- Emit notifications only after the final stabilized derived state is evaluated.
- Cap how long pending changes may be held (max-wait) so continuous editing still flushes a summary.

Each qualifying day still produces its own derived event as the audit/dedupe record; only delivery is aggregated.

A reasonable default sliding window for v1 is 120 seconds with a 10-minute max-wait cap, unless changed later.

### 12.2 Notify-worthy transitions

Support notifications for these transitions at minimum:

- no meetup candidate -> meetup candidate exists
- non-viable -> viable
- viable -> non-viable

Optional later:
- new note/comment
- day is today and becomes viable

### 12.3 Anti-storm rules

Implement suppression rules:
- do not send repeated “candidate exists” notifications for the same day during the same debounce cycle
- collapse multiple day-transitions for one circle in the same cycle into a single aggregated summary notification
- do not notify on every attendee count change
- do not notify on every raw state change
- allow per-member notification preferences

Notification transport choice is left open for a separate question, but the domain events and debounce behavior are part of this contract.

## 13. Past-day behavior

Past days are accessory, not a core planning surface.

Rules:
- Past days are archived automatically.
- Past days are read-only for normal users in v1.
- Past days may remain visible for reference.
- No explicit finalization state is required.
- If the current date passes a day, that day is effectively historical.

## 14. Permissions

### Circle owner/admin
May:
- edit circle settings
- manage invites
- manage membership roles
- manage any member's host day constraints

### Member
May:
- join via invite after authentication
- set own availability
- choose own pseudonym within the circle
- view circle calendar and day details
- add day notes/comments subject to final policy
- manage own host day constraints

No user may edit another member’s availability in v1.

## 15. API and domain behavior expectations

The coding agent should implement the domain so that:

- circle timezone is authoritative for day semantics
- availability writes are idempotent for the same resulting state
- deleting availability is safe and equivalent to `empty`
- viability can be computed on demand and also cached if useful
- notification evaluation can be triggered asynchronously after writes
- all date validation uses circle-local date rules, not client-local assumptions

## 16. Frontend behavior expectations

The frontend must be mobile-first.

Minimum behaviors:
- sign-in flow
- circle list
- circle calendar view
- tap-to-cycle on day cells
- visible indication of the signed-in member’s own state on each day
- visible aggregate viability marker on each day
- viable-only filter toggle
- day detail view with attendee pseudonyms and counts
- note/comment display and creation if notes are included in the first cut

The visual design should remain simple and low-overhead. Avoid dense admin-heavy interfaces.

## 17. Persistence guidance

A practical initial relational model is:

- users
- auth_identities
- circles
- circle_memberships
- circle_invites
- day_availabilities
- host_day_constraints
- day_notes or day_comments
- notification_events
- notification_deliveries

Exact schema naming may vary, but the separation of concerns should
remain.

### users

Holds project-local profile data only. There is no password field,
no password hash, and no credential of any kind on this table.
Identity is established exclusively via `auth_identities`.

### auth_identities

Maps an external OIDC identity to a local user record. Each row
represents one `(provider, subject)` pair:

- `user_id` — foreign key to `users`
- `provider` — issuer identifier (e.g. Keycloak realm URL)
- `subject` — the `sub` claim from the OIDC token
- `created_at`

One user may have at most one identity per provider in v1. The
application creates or updates a `users` row on first successful
token validation, then upserts the matching `auth_identities` row.

## 18. Non-functional expectations

- Self-hostable with Docker; the full stack (app + database +
  Keycloak) is defined in a single `docker-compose.yml`
- Keycloak is a required service. Its operational complexity is
  accepted as a deliberate trade-off (see section 1a). A
  `docs/operator/keycloak.md` runbook must exist before v1 ships.
- Reasonable defaults for low traffic
- Clean environment-based configuration
- Database migrations included
- Basic audit timestamps on persisted entities
- Privacy-conscious defaults
- No unnecessary tracking

## 19. Explicit v1 exclusions to prevent scope creep

Do not implement these in v1 unless required by the coding agent for structural reasons:

- required attendees
- per-day explicit host assignment
- calendar sync with Google, Apple, or Microsoft
- public signup or anonymous participation
- score-based day ranking
- rich text *notes/comments* (rich text is allowed only for day
  descriptions, section 10.1)
- backup host distinction
- complex moderation/reporting
- advanced historical analytics
- websocket-first realtime presence

## 20. Delivery criterion

v1 is complete when a small private circle can:

- create a circle
- invite members
- join after authentication
- choose per-circle pseudonyms
- tap days to mark availability
- see which days are currently viable
- optionally filter to viable days
- see circle-day details
- receive non-spammy notifications on meaningful derived transitions
- use circle defaults with optional per-day overrides
- operate the system in a self-hosted setup


