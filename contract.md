# Meeting Availability App v1 Implementation Contract

## 1. Purpose

Build a small, mobile-first web application for private circles of friends to
discover viable meetup days with minimal clerical overhead.

The core interaction is per-day availability marking inside a circle. A day
becomes an emergent meetup candidate when at least one member marks positive
availability for that day.

The application is invite-only. It supports self-hosting and should be simple to
operate.

## 2. Chosen stack

Use these technologies for v1:

- Backend: FastAPI
- Database: PostgreSQL
- Frontend: Vue.js
- UI framework: Vuetify
- Containerization: Docker and docker-compose or Docker stack compatible setup

Rationale:
- These choices align with existing operator experience.
- They are mature and sufficient for the expected scale.
- No strong argument exists to deviate for v1.

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
- Optional per-day overrides
- Derived viability markers
- “Display only viable days” toggle
- Day detail view
- Optional day notes/comments
- Notifications on meaningful derived transitions
- Past day archive behavior
- Three-month forward planning window

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
- future days up to 3 months ahead

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
- Future dates beyond the 3-month horizon must be rejected by validation.
- Past dates should be treated as read-only for normal users in v1.

## 9. Day overrides model

Day overrides are needed because circles may have traditions that sometimes
change for one specific day.

Persist a lightweight per-day overrides record keyed by `(circle_id, local_date)`.

Allowed override fields in v1:
- override_host_needed: nullable boolean
- override_minimum_attendees: nullable integer
- override_soft_max_attendees: nullable integer
- override_hard_max_attendees: nullable integer
- note or metadata pointer if needed

Rules:
- Overrides are optional.
- Absence of an override means circle defaults apply.
- Overrides must not create a phantom meetup by themselves.
- A day only counts as an emergent meetup candidate if at least one member has non-empty availability on that day.
- Day note creation alone must not create a meetup candidate.

Permissions:
- Only circle owner or admin may edit day overrides in v1.

## 10. Day notes/comments

Support lightweight notes attached to a circle-day.

Minimum v1 requirement:
- plain text note or simple comment entries
- stored separately from availability rows
- associated with `(circle_id, local_date)`

Rules:
- Notes are optional.
- Notes must be viewable from the day detail view.
- Rich text is not required for v1.
- Quill or richer editing is explicitly deferred.

Permissions:
- Any circle member may add a note/comment in v1 unless later policy says otherwise.
- Edit/delete policy is left as an open question unless needed for the initial implementation. Prefer a simple append-only model if uncertain.

## 11. Viability rules

Viability is derived from current state. There is no explicit finalization flow in v1.

For a given circle-day, compute:

- attendee_count = number of members with state in {attending, hosting}
- hosting_count = number of members with state = hosting
- host_required = resolved value from day override or circle default
- min_attendees = resolved value from day override or circle default
- soft_max = resolved value from day override or circle default
- hard_max = resolved value from day override or circle default

### 11.1 Viability decision

A day is `viable` if all of the following are true:

- at least one non-empty availability exists
- if `min_attendees` is set, `attendee_count >= min_attendees`
- if `host_required` is true, `hosting_count >= 1`
- if `hard_max` is set, `attendee_count <= hard_max`

### 11.2 Warning markers

A day is still viable but should show a warning marker if:
- `soft_max` is set and `attendee_count > soft_max`

A day may also show a subtle informational marker if:
- more than one hosting-capable member has marked `hosting` and no explicit host is designated

There is no explicit host designation workflow in v1. This marker is purely informative.

### 11.3 Empty days
A day with zero non-empty availabilities is not a meetup candidate and is not viable.

## 12. Notification contract

Notifications must be based on derived state transitions, not raw tap events.

### 12.1 Debounce requirements

Use a coarse debounce per `(circle_id, local_date)` measured in seconds, not milliseconds.

Required behavior:
- Save availability changes immediately.
- Reflect state changes immediately in the acting user’s UI.
- Delay derived notification evaluation for a debounce window.
- Collapse repeated changes within the debounce window into one evaluation.
- Emit notifications only after the final stabilized derived state is evaluated.

A reasonable default debounce window for v1 is 10 seconds unless changed later.

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
- edit day overrides

### Member
May:
- join via invite after authentication
- set own availability
- choose own pseudonym within the circle
- view circle calendar and day details
- add day notes/comments subject to final policy

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
- day_overrides
- day_notes or day_comments
- notification_events
- notification_deliveries

Exact schema naming may vary, but the separation of concerns should remain.

## 18. Non-functional expectations

- Self-hostable with Docker
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
- rich text comments
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


