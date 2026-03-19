# Admin

The admin service provides a web-based UI for managing the Jarvis platform. It offers dashboards for service status, settings management, node oversight, and system configuration.

## Quick Reference

| | |
|---|---|
| **Port** | 7710 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-admin/` |
| **Framework** | FastAPI + Uvicorn |
| **Tier** | 5 - Clients |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for JWT validation |

## Dependencies

- **jarvis-config-service** -- service discovery
- **jarvis-auth** -- user JWT validation
- **jarvis-settings-server** -- reads and writes runtime settings

## Dependents

- **Administrators** -- browser-based management interface

## Impact if Down

No web-based administration. All services continue operating normally. Settings can still be managed via direct API calls or database access.
