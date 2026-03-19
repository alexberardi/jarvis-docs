# Config Service

The config service is the service discovery hub for all Jarvis services. Every service queries it at startup to resolve URLs for other services it needs to communicate with. It is the single Tier 0 dependency -- if config service is down, no service can discover any other.

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
| `GET` | `/services` | List all registered services and their URLs |
| `GET` | `/services/{name}` | Get URL for a specific service |
| `POST` | `/services` | Register or update a service (admin) |
| `DELETE` | `/services/{name}` | Deregister a service (admin) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for validating admin/app requests |
| `JARVIS_CONFIG_URL_STYLE` | `dockerized` returns `host.docker.internal` URLs for Docker consumers |

## Dependencies

- **PostgreSQL** -- stores service registry

## Dependents

Every service depends on config service for URL discovery:

- jarvis-auth, jarvis-logs, jarvis-command-center, jarvis-llm-proxy-api, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-notifications, jarvis-settings-server, jarvis-mcp, jarvis-admin

## Impact if Down

All inter-service communication that relies on dynamic URL discovery will fail. Services that have already cached URLs may continue operating until their cache expires. New service startups will fail to resolve dependencies.
