# Notifications

The notifications service manages push notifications and an inbox system. It handles device token registration (for mobile push via Expo), notification delivery, and persistent inbox items for asynchronous results like deep research.

## Quick Reference

| | |
|---|---|
| **Port** | 7712 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-notifications/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL |
| **Tier** | 3 - Specialized |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v0/notifications/send` | Send a push notification |
| `POST` | `/api/v0/device-tokens` | Register a device token (Expo push) |
| `DELETE` | `/api/v0/device-tokens/{token}` | Unregister a device token |
| `GET` | `/api/v0/inbox` | List inbox items for a user |
| `GET` | `/api/v0/inbox/{id}` | Get a specific inbox item |
| `POST` | `/api/v0/inbox` | Create an inbox item |
| `PATCH` | `/api/v0/inbox/{id}/read` | Mark an inbox item as read |
| `DELETE` | `/api/v0/inbox/{id}` | Delete an inbox item |

## Push Delivery

Push notifications are forwarded to `jarvis-notifications-relay`, a stateless Expo Push API proxy that handles APNs/FCM delivery. The relay can run locally or in the cloud.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |
| `JARVIS_CONFIG_URL` | Config service URL |
| `NOTIFICATIONS_RELAY_URL` | URL of the notifications relay service |

## Dependencies

- **PostgreSQL** -- device tokens, notification log, inbox items
- **jarvis-auth** -- app-to-app auth validation
- **jarvis-config-service** -- service discovery
- **jarvis-logs** -- structured logging (optional)
- **jarvis-notifications-relay** -- Expo push delivery (optional)

## Dependents

- **jarvis-command-center** -- sends notifications for deep research results and alerts
- **jarvis-node-mobile** -- reads inbox, manages device tokens

## Mobile Experience

<div class="screenshot-grid" markdown>

<figure markdown>
  ![Inbox](../assets/images/screenshots/inbox.png){ width="280" loading=lazy }
  <figcaption>Inbox — deep research results with category chips and swipe-to-delete</figcaption>
</figure>

</div>

## Impact if Down

Push notifications are not sent. Inbox items are not created or retrievable. Deep research results have no delivery mechanism. Voice commands and other services continue operating normally.
