# Installation

## Quick Start

The `jarvis` CLI handles everything — token generation, database creation, migrations, and service startup:

```bash
git clone https://github.com/alexberardi/jarvis.git
cd jarvis
./jarvis quickstart
```

This runs three phases:

1. **`init`** — Generates auth tokens, creates `.env` files, starts PostgreSQL/Redis/MinIO, runs Alembic migrations
2. **`start --all`** — Starts all services in dependency order
3. **LLM wizard** — Prompts you to select and download a language model

## Manual Setup

If you prefer step-by-step control:

### 1. Initialize infrastructure

```bash
./jarvis init
```

This creates:

- `~/.jarvis/tokens.env` — Generated auth tokens (JWT secrets, API keys, app-to-app credentials)
- `~/.jarvis/databases.env` — Database names for each service
- `.env` files in each service directory (from `.env.example` templates)
- PostgreSQL databases and runs all Alembic migrations

### 2. Start services

```bash
# Start everything
./jarvis start --all

# Or start a specific service
./jarvis start jarvis-command-center
```

Services start in dependency order (tiers):

| Tier | Services | Description |
|------|----------|-------------|
| 0 | config-service | Service discovery |
| 1 | auth, logs | Authentication, logging |
| 2 | command-center, llm-proxy | Voice processing, LLM inference |
| 3 | whisper, tts, ocr, recipes, notifications | Specialized services |
| 4 | settings-server, mcp | Management tools |
| 5 | admin | Web UI |

### 3. Verify

```bash
./jarvis health
```

This hits every service's `/health` endpoint and reports status.

## Platform Notes

### macOS (Apple Silicon)

GPU-dependent services run **locally** (not in Docker) to access Metal and Apple Vision:

- `jarvis-llm-proxy-api` — Uses MLX or llama.cpp with Metal acceleration
- `jarvis-ocr-service` — Uses Apple Vision framework

The `jarvis` CLI detects Darwin and handles this automatically.

### Linux (NVIDIA GPU)

Everything runs in Docker. GPU services use `nvidia-docker` for CUDA passthrough:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

## Next Steps

- [Register a node and send your first command](first-command.md)
- [Understand configuration and network modes](configuration.md)
