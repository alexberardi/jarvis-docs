# Settings Server

The settings server aggregates runtime settings from across all services. It provides a unified API for the admin UI to read and update configuration without directly accessing individual service databases.

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
| `GET` | `/api/v0/settings` | List all settings |
| `GET` | `/api/v0/settings/{key}` | Get a specific setting |
| `PUT` | `/api/v0/settings/{key}` | Update a setting |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL for service discovery |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for JWT validation |

## Dependencies

- **jarvis-config-service** -- discovers service URLs to proxy settings requests
- **jarvis-auth** -- validates JWT tokens for admin access

## Dependents

- **jarvis-admin** -- web UI reads and writes settings through this service

## Impact if Down

The admin web UI cannot read or modify runtime settings. Services continue using their current settings. Direct database access is still possible as a workaround.
