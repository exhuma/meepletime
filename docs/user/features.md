# Tips & Lesser-Known Features

Once you've found your way around (see
[Getting Started](index.md)), these are the features that aren't
obvious at first glance but make MeepleTime much more useful.

## Hosts can set per-session limits

Most of the time a circle's defaults (minimum attendees, soft and hard
maximums) are enough. But a host's situation can change for a single
day — a smaller room while you're mid-renovation, fewer chairs than
usual, and so on.

If you are hosting a day, you can attach **personal host constraints**
to that one day to override the circle defaults for your own hosting,
without changing anything for the rest of the circle. Open the day's
options (long-press or right-click the day, then **edit constraints**)
and adjust:

- **minimum attendees** for the day to be worth it,
- **soft maximum** — above this the day is flagged as busy but still
  viable,
- **hard maximum** — above this you can no longer host that day.

These combine with the circle defaults by taking the **more
restrictive** value, and they only affect *your* hosting of *that*
day. Other hosts and other days are unaffected. (Overriding the
**timezone** per session — e.g. for a hiking group meeting in
different places — is not available yet.)

## There is no in-app chat — by design

MeepleTime answers *when* you can meet. It deliberately leaves the
conversation — *what* to bring, *where* exactly, last-minute changes —
to the channels you already use: WhatsApp, Telegram, Signal, Discord,
Facebook, and the like.

To make that easy, a circle can publish **external links** to its
group chat(s). Treat those as the place for discussion; MeepleTime
stays a focused scheduling surface rather than yet another inbox.

## Notifications on meaningful changes

Rather than pinging you on every single tap, MeepleTime watches for
**meaningful changes in a day's status** and notifies on transitions
that actually matter, such as:

- a day becoming a possible meetup for the first time,
- a day turning **viable**, and
- a previously viable day turning **non-viable** again.

Rapid back-and-forth edits are collapsed together, so you get one
notification once the dust settles — not a storm.

> **Alpha note:** the events that *decide* when to notify are in place,
> but the actual delivery channel (email, push, etc.) is **not wired up
> yet**. In this alpha you will not receive messages — keep an eye on
> the circle directly, and watch this space.

## Your profile picture

Click your **avatar** in the top bar and choose **Profile** to upload a
photo. MeepleTime shows the best avatar it can find, in order: your
uploaded photo, then the picture from your login provider (if any), then
a [gravatar](https://gravatar.com/) for your email, and finally your
initials. Remove your upload at any time to fall back down that chain.

## Past days are read-only

Once a day has passed it becomes part of the archive: still visible for
reference, but no longer editable. There's no separate "finalise"
step — viability is always just a reflection of the current marks.
