# Settings Server

!!! warning "Deprecation candidate"
    Nothing in the stack calls jarvis-settings-server today — settings reads and writes go through **config-service's settings gateway** (`/v1/settings/*`, port 7700). This service remains deployed for backward compatibility but is slated for removal. Prefer the config-service settings API for new work.

The settings server aggregates runtime settings from across all services. It provides a unified API to read and update configuration without directly accessing individual service databases.

## Quick Reference

| | |
|---|---|
| **Port** | 7708 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-settings-server/` |
| **Framework** | FastAPI + Uvicorn |
| **Tier** | 4 - Management |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/settings/` | List settings across services |
| `GET` | `/v1/settings/{service_name}` | Get all settings for a service |
| `PUT` | `/v1/settings/{service_name}/{key}` | Update a setting |
| `GET` | `/v1/settings/{service_name}/url` | Resolve the service's settings URL |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL for service discovery |
| `JARVIS_AUTH_SECRET_KEY` | JWT validation key — must match jarvis-auth's `AUTH_SECRET_KEY` (validation is local, no auth round-trip) |

## Dependencies

- **jarvis-config-service** -- discovers service URLs to proxy settings requests
- **jarvis-auth** -- validates JWT tokens for admin access

## Dependents

None — the admin UI reads and writes settings through config-service's `/v1/settings/*` gateway, not this service.

## Impact if Down

None in practice (see the deprecation note above). Services continue using their current settings.
