# MCP

The MCP (Model Context Protocol) service provides tool integration for Claude Code, enabling AI-assisted development and debugging of the Jarvis platform. It exposes health checks, log queries, Docker management, database access, and service introspection as MCP tools.

## Quick Reference

| | |
|---|---|
| **Port** | 7709 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-mcp/` |
| **Framework** | FastAPI + Uvicorn |
| **Tier** | 4 - Management |

## Tool Groups

Tools are organized into groups. The active set is controlled by `JARVIS_MCP_TOOLS` (comma-separated group names). All groups except `tests` and `db` are enabled by default.

### debug

| Tool | Description |
|------|-------------|
| `debug_health` | Check health of all or specific services |
| `debug_service_info` | Get detailed info about a registered service |

### health

| Tool | Description |
|------|-------------|
| `health_check_all` | Ping every registered service and report status |
| `health_check_service` | Health check a specific service by name |

### logs

| Tool | Description |
|------|-------------|
| `query_logs` | Query logs with filters (service, level, time range) |
| `logs_tail` | Get recent log lines from a service |
| `get_log_stats` | Log entry counts by service and level |

### docker

| Tool | Description |
|------|-------------|
| `docker_ps` | List jarvis containers |
| `docker_logs` | Get recent container logs |
| `docker_restart` | Restart a container |
| `docker_stop` / `docker_start` | Container lifecycle |
| `docker_compose_up` / `docker_compose_down` | Compose stack management |
| `docker_compose_list` | List services with compose files |

### command

| Tool | Description |
|------|-------------|
| `run_command` | Run a whitelisted shell command on the Jarvis host |

### db

*Disabled by default.* Enables direct database queries against Jarvis PostgreSQL databases.

### datetime

| Tool | Description |
|------|-------------|
| `get_current_time` | Current server time in ISO 8601 |
| `format_datetime` | Format a timestamp |

### math

Basic arithmetic and unit-math helpers for use in Claude Code workflows.

### conversion

Unit conversion tools (temperature, length, weight, etc.).

### tests

*Disabled by default.* Enables running Jarvis service test suites from within Claude Code.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL for service discovery |
| `JARVIS_AUTH_APP_ID` | App ID for authenticating to other services |
| `JARVIS_AUTH_APP_KEY` | App key for authenticating to other services |
| `JARVIS_MCP_TOOLS` | Comma-separated list of enabled tool groups (default: all except `tests,db`) |
| `JARVIS_ROOT` | Root directory of the Jarvis installation (for Docker Compose operations) |
| `POSTGRES_HOST` | PostgreSQL host for `db` tool group |
| `POSTGRES_PORT` | PostgreSQL port |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | Default database name |

## Dependencies

- **jarvis-config-service** — service discovery for health checks and introspection
- **jarvis-logs** — log query backend
- **jarvis-auth** — auth headers for protected service calls
- **Docker socket** — container management

## Dependents

- **Claude Code** — primary consumer (development tooling)

## Impact if Down

Claude Code loses access to Jarvis MCP tools. No effect on production services or end users.
