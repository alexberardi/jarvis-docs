# Auth

The auth service handles all authentication for the Jarvis platform: user JWT tokens (login, register, refresh, logout), app-to-app authentication between services, and node authentication for Pi Zero devices.

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
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v0/auth/register` | Register a new user |
| `POST` | `/api/v0/auth/login` | Login, returns JWT access + refresh tokens |
| `POST` | `/api/v0/auth/refresh` | Returns new access token **+ a newly rotated refresh token** — client must persist the new refresh token or the next refresh will fail |
| `POST` | `/api/v0/auth/logout` | Logout (invalidate refresh token) |
| `POST` | `/internal/validate-app` | Validate app-to-app credentials |
| `POST` | `/internal/validate-node` | Validate node credentials |
| `GET` | `/api/v0/users/{id}` | Get user info by ID |

## Token Rotation

Refresh tokens are **rotated on every `/auth/refresh` call** (since 2026-05). Each refresh mints a new refresh token chained to the previous one by a `family_id`. Clients **must** persist and use the newly returned refresh token — replaying an already-rotated token returns `401`.

A 10-second in-process grace window (`REFRESH_TOKEN_GRACE_SECONDS`) lets a benign double-submit (two concurrent refresh callers, a lost response) re-get the cached successor without failing. This grace cache is in-process only — auth must stay **single-worker** until backed by Redis/Postgres.

**Stale replay behavior (default):** a replay of an already-rotated token is rejected (`401`) but does **not** revoke the entire token family. The live tail of the chain keeps working, so the session survives auth restarts and benign double-submits over flaky connections. Enable strict whole-family revocation with `REFRESH_TOKEN_REVOKE_FAMILY_ON_REUSE=true` if you need theft detection and can accept periodic spurious logouts from mobile clients on unreliable links.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `MIGRATIONS_DATABASE_URL` | PostgreSQL connection string for Alembic migrations (use `localhost` even when running in Docker) |
| `AUTH_SECRET_KEY` | JWT signing key — generate with `openssl rand -hex 32` |
| `AUTH_ALGORITHM` | JWT signing algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL in days (default `14`). Keep `>=7` so mobile users are not logged out weekly. |
| `REFRESH_TOKEN_GRACE_SECONDS` | Grace window for benign double-submits of a just-rotated token (default `10`). |
| `REFRESH_TOKEN_REVOKE_FAMILY_ON_REUSE` | When a stale rotated token is replayed, revoke the **entire token family** (default `false`). Off is recommended for most setups — a mobile client on a flaky link replays far more often than tokens are stolen. Enable only if you need stricter theft response and can tolerate the resulting spurious logouts. |
| `JARVIS_AUTH_ADMIN_TOKEN` | Token for admin endpoints — generate with `openssl rand -hex 32` |
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

## Impact if Down

- No new user logins or token refreshes
- App-to-app authentication validation fails (services cannot verify each other)
- Node authentication fails (Pi Zero devices cannot connect)
- Services with cached/valid JWTs may continue briefly
