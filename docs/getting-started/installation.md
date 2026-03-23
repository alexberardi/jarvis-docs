# Installation

There are several ways to install Jarvis, from a one-liner to a full source checkout. Pick the one that fits your setup.

## Option 1: One-Line Install (Recommended)

Download the `jarvis-admin` binary, which includes a guided setup wizard:

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```

This detects your OS and architecture, downloads the latest release, and installs to `~/.jarvis/bin/`. Then start the wizard:

```bash
jarvis-admin
```

Open [http://localhost:7711](http://localhost:7711) in your browser — the setup wizard walks you through selecting services, configuring your hardware, and starting the stack.

!!! info "Prerequisites"
    Docker and Docker Compose (v2+) must be installed. The installer warns you if Docker is missing.

## Option 2: npx (No Install)

If you have Node.js 22+, run directly without installing anything:

```bash
npx @alexberardi/jarvis-admin
```

Same setup wizard, no binary on disk.

## Option 3: Docker

Run the admin panel as a container:

```bash
docker run -d \
  --name jarvis-admin \
  -p 7711:7711 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/alexberardi/jarvis-admin:latest
```

Open [http://localhost:7711](http://localhost:7711) to access the setup wizard.

!!! warning
    Mounting the Docker socket gives the container access to manage other containers. This is required for the wizard to start Jarvis services.

## Option 4: GitHub Releases (Manual)

Download a standalone binary from the [Releases page](https://github.com/alexberardi/jarvis-admin/releases):

| Platform | Binary |
|----------|--------|
| macOS (Apple Silicon) | `jarvis-admin-darwin-arm64` |
| Linux (x86_64) | `jarvis-admin-linux-x64` |
| Linux (ARM64 / Pi 5) | `jarvis-admin-linux-arm64` |

```bash
chmod +x jarvis-admin-*
./jarvis-admin-*
```

## Option 5: From Source (Developers)

For contributing or hacking on Jarvis itself:

```bash
git clone https://github.com/alexberardi/jarvis.git
cd jarvis
./jarvis quickstart
```

This runs three phases:

1. **`init`** — Generates auth tokens, creates `.env` files, starts PostgreSQL/Redis/MinIO, runs Alembic migrations
2. **`start --all`** — Starts all services in dependency order
3. **LLM wizard** — Prompts you to select and download a language model

### Manual Setup

If you prefer step-by-step control:

#### 1. Initialize infrastructure

```bash
./jarvis init
```

This creates:

- `~/.jarvis/tokens.env` — Generated auth tokens (JWT secrets, API keys, app-to-app credentials)
- `~/.jarvis/databases.env` — Database names for each service
- `.env` files in each service directory (from `.env.example` templates)
- PostgreSQL databases and runs all Alembic migrations

#### 2. Start services

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
| 5 | admin, web | Web UIs |

#### 3. Verify

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
