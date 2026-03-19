# CLI Reference

The `./jarvis` script is the main entry point for managing Jarvis services. It handles service orchestration, environment setup, testing, and diagnostics.

## Commands

### `quickstart`

Full setup from scratch: runs `init`, starts all services, and launches the LLM setup wizard.

```bash
./jarvis quickstart
```

### `init`

Generate app-to-app tokens, create `.env` files for all services, start infrastructure (PostgreSQL, Redis, MinIO, Mosquitto), and run database migrations.

```bash
./jarvis init
./jarvis init --force    # Overwrite existing .env files
./jarvis init --custom   # Prompt for custom database names
```

### `start`

Start one or more services in dependency order (Tier 0 first, then Tier 1, etc.).

```bash
./jarvis start jarvis-auth
./jarvis start --all
./jarvis start jarvis-auth --standalone   # With its own PostgreSQL
./jarvis start --all --no-network         # Host networking mode
```

### `stop`

Stop services in reverse dependency order.

```bash
./jarvis stop jarvis-auth
./jarvis stop --all
```

### `restart`

Stop then start a service (or all services).

```bash
./jarvis restart jarvis-command-center
./jarvis restart --all
```

### `rebuild`

Rebuild Docker images and restart services. Useful after code changes to Dockerfiles.

```bash
./jarvis rebuild jarvis-auth
./jarvis rebuild --all
```

### `status`

Show the running status of all registered services.

```bash
./jarvis status
```

### `health`

Hit the health endpoint of each service and report results.

```bash
./jarvis health
```

### `logs`

Tail Docker logs for a specific service.

```bash
./jarvis logs jarvis-command-center
```

### `doctor`

Run system diagnostics: checks Docker, PostgreSQL, required ports, disk space, and service connectivity.

```bash
./jarvis doctor
```

### `test`

Run tests for a service or all services. Handles virtual environment activation and test runner configuration automatically.

```bash
./jarvis test jarvis-auth
./jarvis test --all
```

## Options

| Flag | Description |
|------|-------------|
| `--standalone` | Start the service with its own PostgreSQL container (isolated development) |
| `--no-network` | Skip the shared `jarvis-net` Docker network; services use `host.docker.internal` |
| `--force` | Force overwrite `.env` files during `init` |
| `--custom` | Prompt for custom database names during `init` |

## Network Modes

The CLI supports three network modes:

| Mode | Flag | How Services Communicate |
|------|------|--------------------------|
| **Bridge** (default) | -- | Shared `jarvis-net` Docker network; services use container names |
| **Host** | `--no-network` | No shared network; services use `host.docker.internal` |
| **Standalone** | `--standalone` | Single service with its own PostgreSQL container |

## Platform Behavior

On **macOS (Apple Silicon)**, the CLI automatically overrides GPU-dependent services to run locally instead of in Docker:

- `jarvis-llm-proxy-api` -- Runs locally for Metal/MLX access
- `jarvis-ocr-service` -- Runs locally for Apple Vision access

On **Linux (NVIDIA GPU)**, all services run in Docker. GPU services use the NVIDIA Container Toolkit for GPU passthrough.

## Service Registry

Services are started in tier order:

| Tier | Services |
|------|----------|
| 0 | Config Service (7700) |
| 1 | Auth (7701), Logs (7702) |
| 2 | Command Center (7703), LLM Proxy (7704) |
| 3 | TTS (7707), Whisper (7706), OCR (7031), Recipes (7030), Notifications (7712) |
| 4 | Settings Server (7708), MCP (7709) |
| 5 | Admin UI (7710) |

Stop order is reversed (Tier 5 first, Tier 0 last).
