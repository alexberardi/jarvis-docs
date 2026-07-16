# MCP

!!! warning "Potentially deprecated"
    jarvis-mcp is a development-tooling service that may be removed in a future release. The tools below still work today, but don't build new integrations against this surface without checking its status first.

The MCP (Model Context Protocol) service provides tool integration for Claude Code, enabling AI-assisted development and debugging of the Jarvis platform. It exposes health checks, log queries, Docker management, database access, and service introspection as MCP tools.

## Quick Reference

| | |
|---|---|
| **Port** | 7709 |
| **Health endpoint** | `GET /health` |
| **MCP transport** | SSE — `GET /sse` + `POST /messages` |
| **Source** | `jarvis-mcp/` |
| **Framework** | Starlette (MCP SSE server) + Uvicorn |
| **Tier** | 4 - Management |

## Network Exposure

`jarvis-mcp` is **unauthenticated** and can drive Docker on the host, so the host port publish is scoped to loopback only (`127.0.0.1:7709`, both dev and prod compose) rather than all interfaces.

- **Claude Code** reaches it via `http://localhost:7709` (or `127.0.0.1:7709`) on the same host.
- **In-stack consumers** (other Jarvis containers) reach it over the Docker network by container name/hostname, not through the published host port.
- It is **not reachable from other hosts on the LAN** — there is no supported way to drive Jarvis MCP tools from a remote machine. If you need remote access, tunnel over SSH (e.g. `ssh -L 7709:localhost:7709 <host>`) rather than re-exposing the port on all interfaces.

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
| `health_check` | Ping every registered service and report status |
| `health_service` | Health check a specific service by name |

### logs

| Tool | Description |
|------|-------------|
| `logs_query` | Query logs with filters (service, level, time range) |
| `logs_tail` | Get recent log lines from a service |
| `logs_errors` | Recent error/warning lines across services |
| `logs_services` | List services that have submitted logs |

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
| `command_test` | Run a single voice-command parse test through command-center |
| `command_test_suite` | Run a suite of command parse tests |
| `command_test_list` | List available command test cases |

### db

*Disabled by default.* Enables direct database queries against Jarvis PostgreSQL databases.

### datetime

| Tool | Description |
|------|-------------|
| `datetime_context` | Current server time + date context |
| `datetime_resolve` | Resolve a natural-language date/time expression |

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
| `JARVIS_APP_ID` | App ID for authenticating to other services |
| `JARVIS_APP_KEY` | App key for authenticating to other services |
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
