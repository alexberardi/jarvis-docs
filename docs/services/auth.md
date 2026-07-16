# Auth

The auth service handles all authentication for the Jarvis platform: user JWT tokens (login, register, refresh, logout), password reset, app-to-app authentication between services, and node authentication for Pi Zero devices.

## Quick Reference

| | |
|---|---|
| **Port** | 7701 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-auth/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL |
| **Tier** | 1 - Core Infrastructure |

## API Endpoints

| Method | Path | Description |
|--------|------|--------------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login, returns JWT access + refresh tokens. Response includes `must_change_password` when the account has a pending admin-issued temp password |
| `POST` | `/auth/refresh` | Returns new access token **+ a newly rotated refresh token** — client must persist the new refresh token or the next refresh will fail. Rejects inactive users and expired temp passwords (401) |
| `POST` | `/auth/change-password` | Verifies the current password, sets a new one, revokes **all** other refresh tokens, and returns a fresh token pair the client must adopt. Clears any pending `must_change_password` flag |
| `POST` | `/auth/logout` | Authenticates with the **refresh token itself** (not a Bearer header), so it works even after the access token has expired. Revokes that token's rotation family, or every session for the user with `all_devices: true`. Always returns `204`, even for an unknown/already-revoked token |
| `GET` | `/superuser/users` | Superuser only. Lists all users with household memberships — backs the admin Users panel |
| `POST` | `/superuser/users/{id}/temp-password` | Superuser only. Issues a show-once temp password for a user (bcrypt-stored, expires after `TEMP_PASSWORD_EXPIRE_HOURS`). Sets `must_change_password` and revokes every existing session for that user. Optional body: `{temp_password?, expires_in_hours?}` |
| `GET` | `/internal/app-ping` | Validate app-to-app credentials (round-trip check used by other services) |
| `POST` | `/internal/validate-node` | Validate node credentials |
| `GET` | `/internal/users/batch` | Resolve user IDs to display names (app-to-app; used for speaker resolution) |

## Password Reset (No Email in the Stack)

There is no email service, so password recovery is superuser-driven instead of a reset-link flow:

1. A superuser calls `POST /superuser/users/{id}/temp-password` (via the admin Users panel or directly) to issue a temp password for a locked-out user. This sets `must_change_password = true` on the account and revokes every existing session.
2. The user logs in with the temp password. The login response's `must_change_password: true` field signals clients (mobile, web) to force the change-password flow before letting the user proceed.
3. The user calls `POST /auth/change-password` with the temp password as `current_password` and a new password. This clears `must_change_password`, revokes all other sessions, and returns a fresh token pair.

If the temp password expires before use (`TEMP_PASSWORD_EXPIRE_HOURS`, default 24h), login returns a distinct `401` telling the user to ask an administrator for a new one.

`change-password` also works as a general self-service password change outside the temp-password flow — it always requires the current password.

## Logout and Session Revocation

`POST /auth/logout` authenticates with the **refresh token** in the request body rather than a Bearer access token, so logout still works after the access token has expired:

- Default: revokes only the presented token's rotation family (that one device/session).
- `all_devices: true`: revokes every refresh token for the user (all sessions).
- Always returns `204` regardless of whether the token was found, valid, or already revoked — the response never reveals token state.

Admin-issued temp passwords and self-service `change-password` both revoke **all** of a user's sessions, not just the current one.

## Token Rotation

Refresh tokens are **rotated on every `/auth/refresh` call** (since 2026-05). Each refresh mints a new refresh token chained to the previous one by a `family_id`. Clients **must** persist and use the newly returned refresh token — replaying an already-rotated token returns `401`.

A 10-second in-process grace window (`REFRESH_TOKEN_GRACE_SECONDS`) lets a benign double-submit (two concurrent refresh callers, a lost response) re-get the cached successor without failing. This grace cache is in-process only — auth must stay **single-worker** until backed by Redis/Postgres.

**Stale replay behavior (default):** a replay of an already-rotated token is rejected (`401`) but does **not** revoke the entire token family. The live tail of the chain keeps working, so the session survives auth restarts and benign double-submits over flaky connections. Enable strict whole-family revocation with `REFRESH_TOKEN_REVOKE_FAMILY_ON_REUSE=true` if you need theft detection and can accept periodic spurious logouts from mobile clients on unreliable links.

## Boot-Time Secret Guard

On startup, auth checks `AUTH_SECRET_KEY` and `JARVIS_AUTH_ADMIN_TOKEN` for known placeholders (`change-me`, `__SET_ME__`, etc.) or values under 16 characters — either one being a forgeable/publicly-known secret would let an attacker sign valid JWTs or hit `/admin/*` endpoints.

- **`JARVIS_ENV` unset or not `production`** (the default): an insecure secret logs a loud warning but the service still boots — so a dev box or a not-yet-hardened self-host install isn't bricked by a shipped default.
- **`JARVIS_ENV=production`**: an insecure secret is a **hard boot failure**. Set this in production deployments to opt into strict enforcement.

Generate strong values with `openssl rand -hex 32`.

## Environment Variables

| Variable | Description |
|----------|--------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `MIGRATIONS_DATABASE_URL` | PostgreSQL connection string for Alembic migrations (use `localhost` even when running in Docker) |
| `AUTH_SECRET_KEY` | JWT signing key — generate with `openssl rand -hex 32` |
| `AUTH_ALGORITHM` | JWT signing algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL in days (default `14`). Keep `>=7` so mobile users are not logged out weekly. |
| `REFRESH_TOKEN_GRACE_SECONDS` | Grace window for benign double-submits of a just-rotated token (default `10`). |
| `REFRESH_TOKEN_REVOKE_FAMILY_ON_REUSE` | When a stale rotated token is replayed, revoke the **entire token family** (default `false`). Off is recommended for most setups — a mobile client on a flaky link replays far more often than tokens are stolen. Enable only if you need stricter theft response and can tolerate the resulting spurious logouts. |
| `TEMP_PASSWORD_EXPIRE_HOURS` | Expiry window for a superuser-issued temp password (default `24`). Login rejects an expired temp password with a distinct `401` telling the user to request a new one. |
| `JARVIS_AUTH_ADMIN_TOKEN` | Token for admin endpoints — generate with `openssl rand -hex 32` |
| `JARVIS_ENV` | Deployment environment (default `development`). Set to `production` to make the [boot-time secret guard](#boot-time-secret-guard) fatal on a weak/placeholder `AUTH_SECRET_KEY` or `JARVIS_AUTH_ADMIN_TOKEN`; otherwise it only warns. |
| `JARVIS_APP_ID` | App identity for service-to-service auth with jarvis-logs (default `jarvis-auth`) |
| `JARVIS_APP_KEY` | App key for service-to-service auth with jarvis-logs |
| `JARVIS_LOG_CONSOLE_LEVEL` | Console log level (default `INFO`) |
| `JARVIS_LOG_REMOTE_LEVEL` | Remote log level sent to jarvis-logs (default `DEBUG`) |

## Dependencies

- **PostgreSQL** -- user accounts, app credentials, node credentials, refresh tokens
- **jarvis-logs** -- structured logging (optional, degrades to console)

## Dependents

Nearly every service depends on auth for request validation:

- jarvis-command-center, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-logs, jarvis-notifications, jarvis-settings-server, jarvis-mcp, jarvis-admin, jarvis-config-service

The admin Users panel (jarvis-admin) and the mobile/web forced-password-change gates (jarvis-node-mobile, jarvis-web) consume the superuser and change-password endpoints directly.

## Impact if Down

- No new user logins or token refreshes
- No password resets or changes; locked-out users cannot recover access
- App-to-app authentication validation fails (services cannot verify each other)
- Node authentication fails (Pi Zero devices cannot connect)
- Services with cached/valid JWTs may continue briefly
