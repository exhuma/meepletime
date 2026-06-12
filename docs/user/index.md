# User Guide — Getting Started

Welcome to MeepleTime — a low-overhead way for a small circle of
friends to find days that work for everyone to meet up.

This page gets a brand-new user from signing in to marking their first
available day. For less obvious features, see
[Tips & lesser-known features](features.md).

## What MeepleTime is (and isn't)

A **circle** is a private group of friends sharing a calendar. On each
day, members mark whether they **can attend** or **can host**, and the
app works out which days are actually *viable* meetups based on the
circle's rules. There is no public sign-up and no discovery — you only
ever see circles you have been invited to.

MeepleTime deliberately has **no chat**. It tells you *when* you can
meet; agreeing on the details happens in your usual group chat (see
[Tips & lesser-known features](features.md)).

## 1. Sign in

MeepleTime has no password of its own. Signing in opens your
organisation's **Keycloak** login page; after you authenticate you are
returned to the app. If your session expires, you are simply asked to
sign in again.

## 2. Join a circle

Circles are invite-only. A circle owner or admin shares an **invite
link** (often as a QR code) with you. Opening it — after signing in —
lets you join. You will be asked to choose:

- a **pseudonym** — the name the rest of the circle sees for you
  (unique within that circle); and
- whether you can **host by default** — i.e. you are generally able to
  host meetups. (You still decide host-or-not per day; this is just the
  default.)

You can also create your own circle from the **Circles** screen and
invite others.

## 3. Mark your availability

Open a circle to see its **calendar**. Tap a day to cycle your own
state for that day:

```
(empty)  →  attending  →  hosting  →  (empty)
```

- **Attending** — you can come if the day goes ahead.
- **Hosting** — you can attend *and* host.
- **Empty** — no availability (the default; tap through to clear).

Changes save immediately. Past days are read-only.

## 4. Read the day markers

A day becomes a possible meetup as soon as **at least one** member is
attending or hosting. The calendar marks days so you can see at a
glance:

- **Viable** — the day satisfies the circle's rules (enough attendees,
  a host if one is required, within limits). These are highlighted.
- **Over soft max** — still viable, but busier than the preferred
  size.
- **Multiple hosts** — more than one person offered to host; agree
  among yourselves who actually does.

A small legend on the calendar explains the icons.

## 5. Two ways to browse: Calendar and List

At the top of a circle you can switch between two tabs:

- **Calendar** — the full month grid, best for tapping availability.
- **List** — an "upcoming days" view that shows only days with at
  least one attendee, in date order. Use the **viable days only**
  filter (the funnel icon) to hide days that don't yet qualify. This
  is the quickest way to answer "so, when *can* we meet?".

## 6. See the details of a day

Tap a day's details (long-press or right-click a day on the calendar,
or tap a row in the List) to open the **day detail** view. There you
can see who is attending or hosting and read or add **notes** for that
day.

That's everything you need to start. When you're comfortable, the
[Tips & lesser-known features](features.md) page covers per-day host
limits, why there's no in-app chat, and notifications.
