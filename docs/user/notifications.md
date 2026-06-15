# Notifications

MeepleTime can tell you when a day in one of your circles becomes a
**viable meetup** (or when a meetup candidate first starts forming),
without you having to watch the calendar.

You are always in control of how — and whether — you are notified.

## When a notification fires

Notifications are based on *derived state*, not on every tap. You are
notified when a day crosses a meaningful threshold, for example:

- a day goes from "no candidate" to "a meetup candidate exists";
- a day becomes **viable**;
- a viable day stops being viable.

Rapid back-and-forth changes are collapsed, so you will not be spammed
while people are still tapping. When several days in a circle change
around the same time, they are gathered into **one summary
notification** that lists all the affected days, rather than a separate
message for each day.

## Choosing your channels

Click your **avatar** in the top bar and choose **Profile** to manage
your channels. Each channel has its own switch:

- **Email** — a message is sent to your account's email address.
- **Browser notifications** — a system notification on the current
  device, even when the MeepleTime tab is closed.
- **Telegram direct messages** — personal DMs from the bots of circles
  you belong to; see **Telegram** below.

Each channel also has a **Test** button that sends a real test
notification right away and tells you whether it worked, so you can
confirm a channel before relying on it.

Your channel choices are **global** — they apply across every circle you
belong to.

## Muting a single circle

Channel switches decide *how* you are reached. To silence one noisy
circle without turning off a channel everywhere, mute that circle from
its own settings. Muting a circle stops all per-user notifications for
it while leaving your other circles untouched.

## Email

When email is enabled and your operator has configured a mail server,
each qualifying transition sends you a short message with a direct link
to the relevant day. If email delivery is not configured by your
operator, the switch has no effect and no mail is sent.

### Notification email

By default, notifications go to your account email — the address is
shown in the **Notifications** section of your profile so you always
know where mail will land. The text field there is only for choosing a
*different* address; leave it blank to keep using your account email.
To use another address:

1. Enter the address and save.
2. A confirmation email is sent to that address — click the link inside
   (valid for 24 hours) to activate it.
3. If the link expires before you click it, use the **Resend link**
   action to get a fresh one.

Once confirmed, that address is used for all email notifications instead
of your account email. If you never set one (or remove it), notifications
continue to go to your account email as long as email notifications are
turned on.

## Browser notifications

Turning on **Browser notifications** asks your browser for permission
and then registers *this device* for background push. Because the
permission and subscription are per-device, enable it on each browser or
phone where you want notifications. They are delivered even when the
MeepleTime tab is closed, as long as the browser is running.

Browser notifications require a secure (HTTPS) connection and a browser
that supports the Web Push standard (current Chrome, Edge, Firefox, and
— on iOS 16.4+ — Safari for installed web apps). If the switch is
disabled, either your browser does not support it or your operator has
not configured it.

## Telegram

A circle's owner or admin sets up Telegram bots from **Edit circle
settings → Notifications — Telegram**. A bot can work in one of two
modes:

- **Group chat** — the bot posts each circle's updates into one shared
  group chat for everyone to see. No per-member opt-in is needed; if you
  would rather not see the posts, an admin can remove the bot or you can
  mute that circle.
- **Direct messages** — members opt in individually to receive personal
  DMs, so only those who choose to are messaged.

### Opting in to direct messages

If a circle you belong to offers a direct-message bot, you can connect
to it from your own profile:

1. Turn on **Telegram direct messages** in your profile.
2. In Telegram, start a private chat with the bot and send it any
   message (a bot cannot message you until you have messaged it first).
3. Back in your profile, press **Connect** next to that bot and pick
   your chat from the detected list. Use **Test** to confirm it works.

You will then receive that circle's updates as a private message. Press
**Disconnect** at any time to stop. You only ever see the bots of
circles you actually belong to.
