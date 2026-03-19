# MCP

The MCP (Model Context Protocol) service provides tool integration for Claude Code, enabling AI-assisted development and debugging of the Jarvis platform. It exposes health checks, log queries, Docker management, and service introspection as MCP tools.

## Quick Reference

| | |
|---|---|
| **Port** | 7709 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-mcp/` |
| **Framework** | FastAPI + Uvicorn |
| **Tier** | 4 - Management |

## MCP Tools

| Tool | Description |
|------|-------------|
| `debug_health` | Check health of all or specific services |
| `debug_service_info` | Get detailed info about a service |
| `query_logs` | Query logs with filters |
| `logs_tail` | Get recent logs from a service |
| `get_log_stats` | Get log statistics |
| `docker_ps` | List jarvis containers |
| `docker_logs` | Get recent container logs |
| `docker_restart` | Restart a container |
| `docker_stop` / `docker_start` | Container lifecycle |
| `docker_compose_up` / `docker_compose_down` | Compose stack management |
| `docker_compose_list` | List services with compose files |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL |
| `JARVIS_AUTH_APP_ID` | App ID for authenticating to other services |
| `JARVIS_AUTH_APP_KEY` | App key for authenticating to other services |

## Dependencies

- **jarvis-config-service** -- service discovery for health checks and introspection
- **jarvis-logs** -- log query backend
- **jarvis-auth** -- auth headers for protected service calls
- **Docker socket** -- container management

## Dependents

- **Claude Code** -- primary consumer (development tooling)

## Impact if Down

Claude Code loses access to Jarvis MCP tools. No effect on production services or end users.
