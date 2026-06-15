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

Open the **gear icon** in the top bar (**Notifications**) to manage your
channels. Each channel has its own switch:

- **Email** — a message is sent to your account's email address.
- **Browser notifications** — a system notification on the current
  device, even when the MeepleTime tab is closed.

Telegram works a little differently — it is set up per circle rather
than from your profile; see **Telegram** below.

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

By default, notifications go to your account email. You can set a
separate **notification email** in the **Notifications** section of your
profile:

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

Telegram is set up **per circle** by an owner or admin, not from your
personal profile. An admin creates a bot, adds it to the group chat your
circle already uses, and links it in the circle's **Telegram
notifications** settings. After that, viability updates for that circle
are posted straight into the group chat for everyone to see.

Because it posts to a shared group, Telegram does not need each member
to opt in individually. If you would rather not see the group posts, an
admin can remove the bot or you can mute that circle.

Some circles instead use **direct-message** bots. For those, turn on
**Telegram direct messages** in your profile, then open the circle's
notification settings, start a private chat with the bot, and link your
personal chat id (for example from @userinfobot). You will then receive
that circle's updates as a private message instead of a group post.
