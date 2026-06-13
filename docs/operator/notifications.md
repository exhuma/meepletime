# Notification delivery

MeepleTime evaluates notification-worthy transitions for every circle
and records them regardless of configuration. **Delivery** to a channel
happens only when that channel is configured here. Each channel is
independent and **inert until configured** — leaving a channel's
variables unset is safe and simply means nothing is sent on it.

All variables use the `MEEPLETIME_` prefix and are read from the
environment (or the `.env` file) like the rest of the backend
configuration.

## Deep links

Notification bodies include a direct link to the relevant day. Set the
public URL of the frontend so those links resolve for your users:

| Variable                | Meaning                              |
| ----------------------- | ------------------------------------ |
| `MEEPLETIME_APP_BASE_URL` | Public base URL of the frontend SPA. |

When unset it defaults to `http://localhost:5173`, which is only useful
for local development.

## Email (SMTP)

Email is a self-hosted SMTP channel using STARTTLS submission. It is
active once `MEEPLETIME_SMTP_HOST` and `MEEPLETIME_SMTP_FROM` are set.

| Variable                   | Default | Meaning                                  |
| -------------------------- | ------- | ---------------------------------------- |
| `MEEPLETIME_SMTP_HOST`     | (unset) | SMTP server hostname. Enables the channel. |
| `MEEPLETIME_SMTP_PORT`     | `587`   | SMTP submission port.                    |
| `MEEPLETIME_SMTP_FROM`     | (unset) | `From` address for notification mail.    |
| `MEEPLETIME_SMTP_USERNAME` | (unset) | Auth username, if your server requires it. |
| `MEEPLETIME_SMTP_PASSWORD` | (unset) | Auth password, if your server requires it. |
| `MEEPLETIME_SMTP_USE_TLS`  | `true`  | Issue `STARTTLS` after connecting.       |

Behaviour notes:

- If both username and password are set, the backend authenticates;
  otherwise it sends unauthenticated (useful for an internal relay).
- All SMTP operations use a short network timeout. A slow or
  unreachable mail server fails that single send and is recorded as a
  failed delivery attempt; it never blocks other channels or the
  evaluation job.

Example (docker-compose environment):

```
MEEPLETIME_SMTP_HOST=smtp.example.com
MEEPLETIME_SMTP_PORT=587
MEEPLETIME_SMTP_FROM=meepletime@example.com
MEEPLETIME_SMTP_USERNAME=meepletime
MEEPLETIME_SMTP_PASSWORD=change-me
MEEPLETIME_SMTP_USE_TLS=true
```

## Web Push (browser notifications)

Web Push delivers background notifications to a user's browser even when
the MeepleTime tab is closed. It is standards-based (VAPID) and needs no
third-party service. The channel is active once all three VAPID
variables are set.

| Variable                    | Meaning                                    |
| --------------------------- | ------------------------------------------ |
| `MEEPLETIME_VAPID_PUBLIC_KEY`  | Base64url application server key (public). |
| `MEEPLETIME_VAPID_PRIVATE_KEY` | Private key — path to a PEM file or the key string. **Server-only; never exposed.** |
| `MEEPLETIME_VAPID_SUBJECT`     | A `mailto:` or `https:` contact, e.g. `mailto:ops@example.com`. |

### Generating a key pair

The `vapid` CLI ships with the backend's dependencies:

```
vapid --gen                    # writes private_key.pem + public_key.pem
vapid --applicationServerKey   # prints the base64url public key
```

Set `MEEPLETIME_VAPID_PUBLIC_KEY` to the `applicationServerKey` output,
point `MEEPLETIME_VAPID_PRIVATE_KEY` at the mounted `private_key.pem`,
and set a contact in `MEEPLETIME_VAPID_SUBJECT`. Only the public key is
ever sent to browsers (via `GET /notifications/webpush/key`).

### HTTPS is required (Traefik)

Service workers and the Push API only work in a **secure context**.
Behind Traefik this means:

- Terminate TLS at Traefik (e.g. Let's Encrypt) and serve the app over
  `https://`. On plain HTTP the browser silently refuses to register the
  service worker and the channel does nothing.
- Forward the standard proxy headers so the app sees the real scheme;
  Traefik sets `X-Forwarded-Proto: https` by default — keep it.
- No special routing is needed for the service worker: it is served by
  the frontend at `/sw.js` (origin root), which the existing `/` router
  already covers.

Subscriptions that a push service later reports as expired (HTTP 410)
are pruned automatically on the next send.

## Telegram (circle-scoped)

Telegram is **not** configured with environment variables. Because one
group of friends may run several circles through a single shared
group-chat bot — or use different bots per circle — each Telegram bot is
configured **inside a circle's settings** by an owner or admin. There is
no global bot and no server-side Telegram variables to set.

How it works end to end:

1. In Telegram, talk to **@BotFather** and create a bot. Copy the bot
   **token** it gives you.
2. Add the bot to the group chat where the circle should receive
   updates, and post any message in that group.
3. In MeepleTime, open the circle, choose **Notification settings**
   (owner/admin only), and add the bot with a label and the token.
4. Click **Detect chat** — the backend calls the bot's `getUpdates` and
   lists the chats it has seen. Pick the group. That stores the chat id.
5. Use the **Test** button to post a real test message to the group and
   confirm delivery before relying on it.

From then on, each notification-worthy transition posts a message to
that group chat. A circle may have several bots; the same bot/token can
be reused across circles by entering it in each.

Operational notes:

- **Outbound only.** The backend only calls `api.telegram.org`
  (`sendMessage`, `getUpdates`). No inbound webhook is used, so there is
  **nothing extra to route or expose through Traefik**.
- **Token storage.** Bot tokens are stored in the database so the
  backend can send as the bot. They are never returned by the API (only
  a masked hint is shown). Protect the database and its backups
  accordingly, and revoke a token via BotFather if it leaks.
- Each send uses a short timeout; an unreachable bot fails only that
  send and is recorded as a failed attempt.
