- [x] [mvp] Add a github workflow that builds two docker images. One for the
      backend, one for the front-end. We assume that keycloak is available
      externally and that the database is provided by the OPS team as a vanilla
      postgresql container. Add a minimal section to the operations manual
      explaining how to bring the stack up.
- [x] [mvp] Aside from the calendar view, we also need a simple list-view of
      upcoming vialble days. This list-view could also have the same toggle to
      include/exclude non-viable days. To avoid showing all dates, the list view
      should only list days with at least one attendee.
- [ ] The time-zone dropdown should be more subtle in the UI. A smaller dropdown
      tucked to the bottom of the dialog (like a system-status-bar or footer).
- [ ] The "state" values "attending" and "hosting" should be "can_attend" and
      "can_host"
- [ ] Implement a real notification sender. Currently `NotificationEvent` and
      `NotificationDelivery` rows are written to the DB but nothing actually
      delivers a message — `delivered_at` is always NULL. A delivery mechanism
      (e.g. email, push, WebSocket) needs to be chosen and wired in.
      Technical details are open.
- [x] [mvp] We need more documentation. One for onboarding new users and one for
      less frequently used features for returning users. At the moment it is not
      clear that...
  - ... Hosts can override constraints (soft-max, hard-max, timezone) per hosted
    session.
  - ... circle members are expected to use outside communication channels
    (WhatsApp, Telegram, Facebook, Discord, ...) as messaging is deliberately
    out of scope of this application.
  - ... notifications are sent out when viability changes (at this time, the
    notification backend is not yet implemented).
- [ ] [backlog] Add a "profile" section where a user can set personal hosting
      constraints. If constraints for a session are evaluated if follows this
      order using the most appropriate agregation function:
  1. First use the curcle constraints
  2. Second apply the constraints from the host's profile
  3. Third, apply the constraints from the session itself
- [ ] [backlog] We should also allow overriding the time-zone in
      host-day-overrides. For example for hiking groups that may not have every
      event in the same location (and thus timezone). We could also auto-detect
      time-zone based on location
