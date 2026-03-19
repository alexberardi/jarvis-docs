# Logs

The logs service provides centralized structured logging for all Jarvis services. It receives log entries over HTTP and stores them in Loki, with Grafana available for visualization. All services use the `jarvis-log-client` library to send logs here.

## Quick Reference

| | |
|---|---|
| **Port** | 7702 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-logs/` |
| **Framework** | FastAPI + Uvicorn |
| **Backend** | Loki (7032) + Grafana (7033) |
| **Tier** | 1 - Core Infrastructure |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v0/logs` | Submit a single log entry |
| `POST` | `/api/v0/logs/batch` | Submit a batch of log entries |
| `GET` | `/api/v0/logs` | Query logs with filters |
| `GET` | `/api/v0/logs/stats` | Log statistics |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LOKI_URL` | Loki push endpoint |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for validating app credentials |

## Dependencies

- **Loki** -- log storage backend
- **Grafana** -- log visualization (optional)
- **jarvis-auth** -- validates app-to-app credentials on incoming log requests

## Dependents

All services send logs here via `jarvis-log-client`:

- jarvis-auth, jarvis-config-service, jarvis-command-center, jarvis-llm-proxy-api, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-notifications, jarvis-settings-server, jarvis-mcp, jarvis-admin

## Impact if Down

Services continue operating normally. Logs fall back to console output (stdout). No log aggregation or querying until the service is restored. Historical logs in Loki remain accessible once the service comes back.
