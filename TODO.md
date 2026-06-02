- ✓ When creating a circle in the UI, the time-zone should default to the
  time-zone of the user.
- The time-zone dropdown should be more subtle in the UI. A smaller dropdown
  tucked to the bottom of the dialog (like a system-status-bar or footer).
- Creating a circle should display more contextual help explaining what the
  different fields mean. This must adapt appropriately between mobile and
  desktop UIs. On a desktop this help text fits well alongside the form. A
  mobile view may display these on the bottom, but the font-size should be
  slightly reduced and the height should be limited to avoid pushing the form
  out of view. If you see any "best practices" for this, take these into
  consideration.
- Aside from the calendar view, we also need a simple list-view of upcoming
  vialble days. This list-view could also have the same toggle to
  include/exclude non-viable days. To avoid showing all dates, the list view
  should only list days with at least one attendee.
- The "state" values "attending" and "hosting" should be "can_attend" and
  "can_host"
- We should also allow overriding the time-zone in host-day-overrides. For
  example for hiking groups that may not have every event in the same location
  (and thus timezone). We could also auto-detect time-zone based on location
- CRITICAL: The calender is not updating the DOM when navigating to other
  circles. It keeps the information of the first loaded circle. The calendar
  view loops over values from a nested dict which probably breaks reactivity.
