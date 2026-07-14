# Config Service

The config service is the service discovery hub for all Jarvis services. Every service queries it at startup to resolve URLs for other services it needs to communicate with. It is the single Tier 0 dependency — if config service is down, no service can discover any other.

## Quick Reference

| | |
|---|---|
| **Port** | 7700 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-config-service/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL |
| **Tier** | 0 - Foundation |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/info` | Service identity (name, version, port) |
| `GET` | `/services` | List all registered services and their URLs |
| `GET` | `/services/{name}` | Get URL for a specific service |
| `POST` | `/services` | Register or update a service (admin) |
| `DELETE` | `/services/{name}` | Deregister a service (admin) |
| `GET` | `/services/health` | Check health of all registered services |
| `GET` | `/services/{name}/health` | Check health of a specific registered service |

## URL Style Query Parameters

The `/services` and `/services/{name}` endpoints accept an optional `style` query parameter to control the format of returned URLs:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `style` | *(default)* | Returns container-name URLs (e.g. `http://jarvis-auth:7701`) — used by Docker services on the shared network |
| `style` | `dockerized` | Returns `host.docker.internal` URLs — used when containers need to reach services running directly on the host (e.g. LLM proxy on macOS) |
| `style` | `remote` | Returns URLs using `JARVIS_REMOTE_HOST` as the hostname. Only rewrites `localhost`-registered rows — a service registered under a container name (e.g. `jarvis-command-center`) has no `localhost` to swap, so it's returned unreachable from off-box. |
| `style` | `external` | Since jarvis-config-client#4 — returns each service's published `external_host`/`external_port` coordinates when set, falling back to the same `localhost` → `remote_host` swap as `remote` otherwise. This resolves container-name HTTP rows correctly too, not just `localhost`-registered infra — the correct style for off-box consumers (LAN voice nodes, dockerized nodes) that need to reach *every* registered service, not just the ones registered as `localhost`. |
| `remote_host` | *hostname* | Override the remote host for this request only (used with `style=remote` or `style=external`) |

## Secret Boot Guard (`JARVIS_CONFIG_ADMIN_TOKEN`)

Added in jarvis-config-service#4, closing the last fail-open-default gap in the audit's fail-open family (same pattern as jarvis-auth's `enforce_secret_security` and jarvis-command-center's [Secret Boot Guard](command-center.md#secret-boot-guard-admin_api_key-jarvis_auth_secret_key)). Previously `.env.example` shipped `JARVIS_CONFIG_ADMIN_TOKEN=change-me-to-something-secure` and the admin auth check accepted any non-empty token — the publicly-known template placeholder authenticated against `POST /services` and `DELETE /services/{name}` on the service that bootstraps the whole cluster.

A boot guard checks `JARVIS_CONFIG_ADMIN_TOKEN` against a placeholder list (`change-me`, `changeme`, `change_me`, `__set_me__`, `change-me-to-something-secure`, `change_me_config_admin_token`, case-insensitive) and a 16-character minimum length:

- **Empty, placeholder, or too short:** always logs a loud warning. **Fatal (startup aborts)** only when `JARVIS_ENV=production`.
- **Strong values:** silent, no warning.

Independent of the boot guard, request-time defense in depth rejects a known-placeholder token presented via `X-Admin-Token` with a `401` **before** the comparison — even outside production, and even if the server itself was misconfigured with that placeholder. This means the shipped placeholder can no longer authenticate anywhere, even on a deploy that never sets `JARVIS_ENV`.

`.env.example` and `env.template` now ship `JARVIS_CONFIG_ADMIN_TOKEN=__SET_ME__`.

**To harden a production deploy:** set `JARVIS_ENV=production` and generate a strong value with `openssl rand -hex 32` for `JARVIS_CONFIG_ADMIN_TOKEN`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for validating admin/app requests |
| `JARVIS_CONFIG_ADMIN_TOKEN` | Admin token for `POST /services` and `DELETE /services/{name}`. Placeholder/short values are rejected at boot in production and at request time always — see [Secret Boot Guard](#secret-boot-guard-jarvis_config_admin_token) |
| `JARVIS_CONFIG_URL_STYLE` | Default URL style for all responses (`dockerized` returns `host.docker.internal` URLs, `external` returns published external coordinates — see [URL Style Query Parameters](#url-style-query-parameters)) |
| `JARVIS_REMOTE_HOST` | Hostname used when `style=remote` or `style=external` is requested |
| `PORT` | API port (default `7700`) |

## Dependencies

- **PostgreSQL** -- stores service registry

## Dependents

Every service depends on config service for URL discovery:

- jarvis-auth, jarvis-logs, jarvis-command-center, jarvis-llm-proxy-api, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-notifications, jarvis-settings-server, jarvis-mcp, jarvis-admin

## Impact if Down

All inter-service communication that relies on dynamic URL discovery will fail. Services that have already cached URLs may continue operating until their cache expires. New service startups will fail to resolve dependencies.
