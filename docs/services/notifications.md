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

### User-facing

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v0/inbox` | List inbox items for the authenticated user |
| `GET` | `/api/v0/inbox/{id}` | Get a specific inbox item |
| `POST` | `/api/v0/inbox` | Create an inbox item |
| `PATCH` | `/api/v0/inbox/{id}/read` | Mark an inbox item as read |
| `DELETE` | `/api/v0/inbox/{id}` | Delete an inbox item |
| `GET` | `/api/v0/inbox/unread-count` | Count of unread inbox items for the user |

### Device token management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v0/tokens` | Register a device token (Expo push) |
| `DELETE` | `/api/v0/tokens` | Unregister a device token (token passed in request body) |
| `GET` | `/api/v0/tokens/me` | List all device tokens for the authenticated user |

### Service-to-service

Called by other services (primarily jarvis-command-center) to deliver notifications:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v0/notify` | Send a push notification to a user |
| `POST` | `/api/v0/notify/batch` | Send notifications to multiple users |

## Push Delivery

Push notifications are forwarded to `jarvis-relay`, a stateless Expo Push API proxy that handles APNs/FCM delivery. The relay can run locally or in the cloud.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |
| `JARVIS_CONFIG_URL` | Config service URL |
| `RELAY_URL` | URL of the relay service for Expo push delivery |
| `RELAY_HOUSEHOLD_JWT` | JWT used to authenticate to the relay service |
| `AUTH_SECRET_KEY` | JWT secret key (must match jarvis-auth's `AUTH_SECRET_KEY`) |
| `AUTH_ALGORITHM` | JWT algorithm (default `HS256`) |
| `ADMIN_API_KEY` | API key for admin endpoints |
| `NOTIFICATION_LOG_RETENTION_DAYS` | Days to retain notification log entries |
| `TOKEN_CLEANUP_INTERVAL_HOURS` | Hours between expired token cleanup runs |

`AUTH_SECRET_KEY` and `ADMIN_API_KEY` must each be a real secret of at least 16 characters. The service refuses to start if either is empty, a known placeholder (`change-me`, `__SET_ME__`), or shorter than 16 characters — generate one with `openssl rand -hex 32`.

## Dependencies

- **PostgreSQL** -- device tokens, notification log, inbox items
- **jarvis-auth** -- app-to-app auth validation
- **jarvis-config-service** -- service discovery
- **jarvis-logs** -- structured logging (optional)
- **jarvis-relay** -- Expo push delivery (optional)

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
