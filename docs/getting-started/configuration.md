# Configuration

## Network Modes

The `jarvis` CLI supports three network modes for service communication:

| Mode | Flag | How Services Communicate |
|------|------|--------------------------|
| **Bridge** (default) | — | Shared `jarvis-net` Docker network; services use container names |
| **Host** | `--no-network` | No shared network; services use `host.docker.internal` |
| **Standalone** | `--standalone` | Single service with its own PostgreSQL container |

### Bridge Mode (Default)

Services communicate via Docker's `jarvis-net` bridge network. Service A reaches Service B by container name (e.g., `http://jarvis-auth:7701`).

```bash
./jarvis start --all
```

### Host Mode

For distributed setups where services run on different machines:

```bash
./jarvis start --all --no-network
```

Services use `host.docker.internal` to reach each other. Useful when some services run locally (e.g., GPU services on macOS).

### Standalone Mode

Run a single service with its own PostgreSQL instance — useful for isolated development:

```bash
./jarvis start jarvis-auth --standalone
```

## Environment Variables

Each service reads from a `.env` file in its directory. The `./jarvis init` command generates these from `.env.example` templates, filling in generated tokens.

### Cross-Service Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Most services | PostgreSQL connection string |
| `SECRET_KEY` | auth | JWT signing key |
| `ADMIN_API_KEY` | command-center | Admin endpoint protection |
| `JARVIS_AUTH_BASE_URL` | Most services | Auth service URL |
| `JARVIS_CONFIG_URL` | Most services | Config service URL |

See [Environment Variables Reference](../reference/env-vars.md) for the complete list.

## Service Discovery

Services find each other through `jarvis-config-service` (port 7700). On startup, each service registers itself and queries for dependencies.

The config service returns URLs based on the network mode:

- **Bridge**: `http://jarvis-auth:7701`
- **Host**: `http://host.docker.internal:7701`

See [Service Discovery](../architecture/service-discovery.md) for details.

## Runtime Settings

Some configuration can be changed at runtime via `jarvis-settings-server` without restarting services. This includes LLM model selection, TTS voice, and command-specific settings.

Settings are managed through:

1. **Mobile app** — Settings sync via encrypted snapshots
2. **Settings server API** — Direct HTTP access
3. **Database** — PostgreSQL settings tables
