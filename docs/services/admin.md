# Admin

The admin service provides both a setup wizard for first-time installation and a web dashboard for ongoing management. It runs as a standalone binary (not a Python/FastAPI service) and manages all other Jarvis services via Docker.

## Quick Reference

| | |
|---|---|
| **Port** | 7711 (installer binary) / 7710 (Docker dev container) |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-admin/` |
| **Framework** | Fastify (backend) + React (frontend), compiled with Bun |
| **Tier** | 5 - Clients |
| **Auto-start** | systemd (Linux) / launchd (macOS) |

## What It Does

### Setup Wizard

On first run (no `~/.jarvis/compose/` directory), the admin server serves a setup wizard that:

1. Detects hardware (platform, GPU, available RAM)
2. Lets you select services to enable
3. Generates `docker-compose.yml`, `.env`, and database init scripts
4. Pulls Docker images
5. Starts services in tiered dependency order
6. Registers all services with config-service (creates app-to-app credentials)
7. Creates a superuser account
8. Downloads an LLM model

### Admin Dashboard

After setup, the same binary serves the admin dashboard:

- **Dashboard** -- Container status overview, service health, LLM status
- **Services** -- Registered services, config/auth status, health checks
- **Models** -- Installed models, suggested downloads, custom HuggingFace downloads
- **Quick Sets** -- Named LLM configuration presets; apply or create to switch the active model without editing raw settings
- **Settings** -- Runtime configuration across all services (via settings-server proxy)
- **Nodes** -- Registered voice nodes

## Quick Sets

The **Quick Sets** page lets you create and apply named LLM configuration presets. A preset bundles a backend, model path, chat format, prompt provider, and context window into a single named profile that can be applied in one click.

### Model Path Dropdown

Added in jarvis-admin#6. The **Model file path** field on the apply panel now shows a dropdown of models installed on disk, populated from `GET /api/models/installed` (served by jarvis-llm-proxy-api). Values are `.models/<name>`-prefixed to match what the backend writes to `model.live.name` / `model.background.name`.

- When models are installed, the dropdown appears and pre-selects the current model if it matches an installed entry.
- Selecting **Other (custom path / HF ID)…** reveals the original free-text input for HuggingFace model IDs or paths not yet downloaded.
- When no models are installed the field falls back to free-text only.
- Freshly downloaded models appear in the dropdown without restarting admin — the endpoint scans `.models/` on each request.

## Architecture

```
jarvis-admin (Bun binary)
├── Server (Fastify)
│   ├── /api/auth/*          → Proxy to jarvis-auth
│   ├── /api/settings/*      → Proxy to jarvis-settings-server
│   ├── /api/install/*       → Setup wizard (generate, pull, start, register)
│   ├── /api/models/*        → Model management (list, download, delete)
│   ├── /api/containers/*    → Docker container status
│   ├── /api/llm-setup/*     → LLM configuration
│   └── /api/services/*      → Service registry (via config-service)
├── Frontend (React SPA)
│   ├── Setup wizard (7 steps)
│   └── Dashboard (5 pages)
└── Docker integration
    ├── Compose generation
    ├── Container management (via Docker socket)
    └── Docker exec (model downloads)
```

## Generated Files

The installer creates these files in `~/.jarvis/compose/`:

| File | Purpose |
|------|----------|
| `docker-compose.yml` | Service definitions, ports, environment, volumes |
| `.env` | Secrets, ports, app-to-app credentials |
| `init-db.sh` | PostgreSQL database creation script |

Service URLs and config are persisted in `~/.jarvis/admin.json`.

## Service Registration

After starting tier 0-1 (config-service, auth), the installer batch-registers all services:

```
POST http://localhost:7700/v1/services/register
Header: X-Jarvis-Admin-Token: <JARVIS_AUTH_ADMIN_TOKEN>
Body: { "services": [{ "name": "jarvis-auth", "host": "host.docker.internal", "port": 7701 }, ...] }
```

This registers each service in config-service's database and creates app-to-app credentials in jarvis-auth. The returned app keys are injected into the `.env` file.

Services use `host.docker.internal` as the registered host so Docker containers can reach each other through the host's port mapping. This also supports future multi-machine deployments where remote services would be re-registered with their actual IP/hostname.

## Docker Compose Generation

The compose file is generated from `service-registry.json` which defines:

- **Image**: GHCR path and tag
- **Ports**: External (configurable) and internal (fixed by Dockerfile)
- **Environment**: Database URLs, config URLs, auth secrets, app credentials
- **Dependencies**: `depends_on` with health check conditions
- **Health checks**: Per-service with appropriate `start_period`
- **GPU config**: NVIDIA deploy resources for LLM proxy (Linux only)
- **Volumes**: Named Docker volumes declared per-service in the registry

### Notable Service Configurations

| Service | Notes |
|---------|-------|
| **command-center** | Runs `alembic upgrade head` before uvicorn; python-based health check (no curl in image); mounts `command-center-prompt-providers` volume at `/app/core/prompt_providers_custom` |
| **llm-proxy** | Starts model service (7705) + API (7704) in one container; 120s health check start period. Emits `MODEL_SERVICE_TOKEN` (generated secret) on both the API and worker for internal auth to the model service — without it the model service 503s all inference while `/health` stays green (fixed in jarvis-admin#11, was previously missing from generated composes). On AMD GPUs also emits `JARVIS_FLASH_ATTN=false` (the gfx1201/RDNA4 HIP flash-attention kernel faults), matching the installer. Discrete-GPU device selection is handled in-image (see [LLM Proxy: Discrete-GPU Auto-Select](llm-proxy.md#discrete-gpu-auto-select-vulkan-rocm)), so the generator does not emit `*_VISIBLE_DEVICES`. |
| **whisper-api** | Since jarvis-admin#12, the sync generator selects Whisper's image variant + device passthrough from an **optional** `WizardState.whisperBackend` (`cpu` | `cuda` | `vulkan` | `rocm`, default `cpu` when unset) — independently of the LLM's auto-detected `gpuType`, mirroring the installer SPA's generator (see [Installer: Whisper GPU Backend](installer.md#whisper-gpu-backend)). Optional and defaulted so the upgrade state-reconstructor and older clients keep working with no fanout. Also wired end-to-end through the admin **reconcile (sync)** flow — a GPU-backend select on the Whisper section of ReconcilePage — so existing installs can switch Whisper's backend without a fresh install. A UI control in the initial setup wizard is a planned follow-up (shared with the installer wizard). |
| **settings-server** | Gets `JARVIS_AUTH_SECRET_KEY` from shared auth secret |
| **postgres** | Uses `pgvector/pgvector:pg16` (command-center needs vector extension) |

### Named Volumes

Services that declare `volumes` in `service-registry.json` get both a per-service volume mount and a top-level named-volume declaration in the generated `docker-compose.yml`. Named volumes persist across container recreates and `docker compose up --force-recreate`.

| Volume | Service | Mount Path | Purpose |
|--------|---------|------------|---------|
| `command-center-prompt-providers` | `jarvis-command-center` | `/app/core/prompt_providers_custom` | Custom prompt providers survive container recreates |

To add custom prompt providers, place them in the Docker volume. The volume is managed by Docker and persists independently of the container image.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Admin server port (default: 7711) |
| `DOCKER_SOCKET` | Docker socket path (default: `/var/run/docker.sock`) |
| `MODELS_DIR` | Override models directory for local fallback |

## Dependencies

- **Docker** -- manages all Jarvis service containers
- **jarvis-config-service** -- service discovery and registration
- **jarvis-auth** -- user authentication, app-to-app credential creation
- **jarvis-settings-server** -- settings aggregation proxy

## Dependents

- **Administrators** -- browser-based management interface
- **Setup wizard** -- first-time installation flow

## Impact if Down

No web-based administration or setup wizard. All services continue operating normally. Settings can still be managed via direct API calls.

## Managing the Service

```bash
# Check status
systemctl --user status jarvis-admin

# Restart
systemctl --user restart jarvis-admin

# View logs
journalctl --user -u jarvis-admin --no-pager --since "10 min ago"

# Stop
systemctl --user stop jarvis-admin
```

## Troubleshooting

### Services show "Connection refused" on Services page

If accessing the admin from a different machine (e.g., `http://192.168.1.10:7711`), the browser health checks resolve `localhost` to your client machine, not the server. Access the admin using the server's actual IP in the URL.

### Docker exec errors (HTTP 101)

The Bun runtime has issues with Docker exec env vars via the `dockerode` library. The admin passes values through command arguments instead of environment variables.

### Model download fails with permission denied

The `.models` directory may be owned by root (created by Docker). Fix with:

```bash
sudo chown -R $USER:$USER ~/.jarvis/compose/.models/
```
