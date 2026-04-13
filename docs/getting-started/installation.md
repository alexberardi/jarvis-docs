# Installation

There are several ways to install Jarvis, from a one-liner to a full source checkout. Pick the one that fits your setup.

## Prerequisites

Before installing, make sure you have Docker and Docker Compose:

=== "Ubuntu / Debian"

    ```bash
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Allow your user to run Docker without sudo
    sudo usermod -aG docker $USER
    newgrp docker

    # Verify
    docker compose version
    ```

=== "macOS"

    Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) which includes Docker Compose v2.

    ```bash
    # Verify
    docker compose version
    ```

=== "Linux (NVIDIA GPU)"

    Follow the Ubuntu/Debian steps above, then install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html):

    ```bash
    # Add NVIDIA repo
    distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Install
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker

    # Verify
    docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
    ```

=== "TrueNAS SCALE (Electric Eel+)"

    TrueNAS SCALE 24.10 (Electric Eel) and later include Docker natively, but the Compose plugin may not be bundled. **Do not install Jarvis as a TrueNAS App** — the sandboxed app environment does not provide Docker socket access, which the installer requires.

    SSH into your TrueNAS server and install the Compose plugin manually:

    ```bash
    # Install docker compose plugin (TrueNAS locks apt, so install the binary directly)
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"

    # Verify
    docker compose version
    ```

    Then follow **Option 3: Docker** below to run the installer via SSH.

    !!! warning "Do not use the TrueNAS Apps UI"
        The TrueNAS Apps catalog runs containers in a sandboxed environment without access to the Docker socket. Jarvis needs socket access to create and manage its service containers. Always install via the SSH shell instead.

!!! info "Minimum Requirements"
    - **CPU**: 4+ cores recommended
    - **RAM**: 8 GB minimum, 16+ GB for LLM inference
    - **Disk**: 20 GB for services + model size (4-20 GB per model)
    - **Docker**: v24+ with Compose v2+
    - **GPU** (optional): NVIDIA GPU with 8+ GB VRAM for local LLM inference

## Option 1: One-Line Install (Recommended)

Download the `jarvis-admin` binary, which includes a guided setup wizard:

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```

This detects your OS and architecture, downloads the latest release, and installs to `~/.jarvis/bin/`. The installer also:

- Sets up **systemd** (Linux) or **launchd** (macOS) for auto-start on boot
- Starts the admin server automatically on port 7711

Open [http://localhost:7711](http://localhost:7711) in your browser to begin the setup wizard.

### Setup Wizard Walkthrough

The wizard guides you through seven steps:

| Step | What it does |
|------|-------------|
| **Welcome** | Introduction and system check |
| **Hardware** | Detects platform, GPU, RAM; recommends LLM backend (GGUF/vLLM) |
| **Services** | Select which services to enable (core + optional) |
| **Review** | Confirm configuration before installing |
| **Install** | Generates Docker Compose, pulls images, starts services in tier order |
| **Account** | Create your superuser account (auto-promoted, auto-logged-in) |
| **LLM** | Select and download a language model |

#### Install Step Details

The installer starts services in dependency order:

1. **Infrastructure** -- PostgreSQL, Redis, Loki, Grafana
2. **Tier 0** -- Config service (service discovery) -- wait for healthy
3. **Tier 1** -- Auth -- wait for healthy
4. **Register** -- Batch-registers all services in config-service, creates app-to-app credentials
5. **Remaining services** -- All other enabled services start in parallel

Services discover each other via `host.docker.internal` (Docker's host gateway), so inter-container communication uses the same ports you configured in the wizard.

#### Model Selection

The LLM step offers pre-configured models with matching prompt providers:

| Model | Size | Backend | Notes |
|-------|------|---------|-------|
| Qwen 3 4B | ~2.5 GB | GGUF | Fast, good for constrained hardware |
| Qwen 3 8B | ~5 GB | GGUF | Balanced speed and quality |
| Qwen 3 14B | ~9 GB | GGUF | High quality, needs 12+ GB VRAM |
| Qwen 2.5 7B | ~4.7 GB | GGUF | Stable, well-tested |
| Llama 3.1 8B | ~5 GB | GGUF | Strong general purpose |
| Hermes 3 8B | ~4.9 GB | GGUF | Excellent tool-calling support |

You can also download models later from the **Models** page in the admin dashboard.

### After Installation

Once the wizard completes:

- **Dashboard**: [http://localhost:7711/dashboard](http://localhost:7711/dashboard) -- container status, service health
- **Services**: [http://localhost:7711/services](http://localhost:7711/services) -- registered services, auth status
- **Models**: [http://localhost:7711/models](http://localhost:7711/models) -- manage LLM models
- **Settings**: [http://localhost:7711/settings](http://localhost:7711/settings) -- runtime configuration

Verify everything is running:

```bash
# From the server
curl -s http://localhost:7700/health  # Config service
curl -s http://localhost:7701/health  # Auth
curl -s http://localhost:7703/health  # Command center
curl -s http://localhost:7704/health  # LLM proxy
```

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

1. **`init`** -- Generates auth tokens, creates `.env` files, starts PostgreSQL/Redis/MinIO, runs Alembic migrations
2. **`start --all`** -- Starts all services in dependency order
3. **LLM wizard** -- Prompts you to select and download a language model

### Manual Setup

If you prefer step-by-step control:

#### 1. Initialize infrastructure

```bash
./jarvis init
```

This creates:

- `~/.jarvis/tokens.env` -- Generated auth tokens (JWT secrets, API keys, app-to-app credentials)
- `~/.jarvis/databases.env` -- Database names for each service
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

- `jarvis-llm-proxy-api` -- Uses MLX or llama.cpp with Metal acceleration
- `jarvis-ocr-service` -- Uses Apple Vision framework

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

### TrueNAS SCALE

TrueNAS SCALE 24.10+ (Electric Eel) includes Docker but runs it in a managed environment. Key differences:

- **Do not use the TrueNAS Apps UI** to install Jarvis. The Apps sandbox does not expose the Docker socket, so the installer cannot create service containers.
- **Always install via SSH shell** using Option 3 (Docker) or Option 1 (one-line install).
- **`apt` is locked** on TrueNAS — install the Docker Compose plugin manually (see Prerequisites tab above).
- **Older TrueNAS SCALE versions** (Dragonfish, Cobia) use k3s instead of Docker and are not supported. Upgrade to Electric Eel or run Jarvis in a VM.

If you previously installed Jarvis as a TrueNAS App and need to clean up, remove it from the TrueNAS Apps UI first, then follow the [Manual Cleanup](#manual-cleanup-without-docker-compose) steps below via SSH.

## Reinstalling

To start fresh while keeping Docker images cached:

```bash
# Stop the admin service
systemctl --user stop jarvis-admin   # Linux
# launchctl unload ~/Library/LaunchAgents/com.jarvis.admin.plist  # macOS

# Remove containers and data
cd ~/.jarvis/compose && docker compose down -v

# Remove generated config
rm -rf ~/.jarvis/compose ~/.jarvis/admin.json ~/.jarvis/bin/jarvis-admin

# Re-install
cd ~ && curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```

## Uninstalling

To completely remove Jarvis:

```bash
# 1. Stop all services and remove containers + volumes
cd ~/.jarvis/compose && docker compose down -v

# 2. Stop and remove the admin service
systemctl --user stop jarvis-admin
systemctl --user disable jarvis-admin
rm ~/.config/systemd/user/jarvis-admin.service
systemctl --user daemon-reload

# 3. Remove all Jarvis data
rm -rf ~/.jarvis

# 4. (Optional) Remove Docker images
docker images | grep jarvis | awk '{print $3}' | xargs docker rmi
docker images | grep pgvector | awk '{print $3}' | xargs docker rmi
```

On macOS, replace the systemd commands with:

```bash
launchctl unload ~/Library/LaunchAgents/com.jarvis.admin.plist
rm ~/Library/LaunchAgents/com.jarvis.admin.plist
```

### Manual Cleanup (Without Docker Compose)

If the install was interrupted or `docker compose` is not available, clean up Docker resources manually:

```bash
# 1. Remove all Jarvis containers
docker ps -a --filter "name=jarvis" -q | xargs -r docker rm -f

# 2. Remove Docker volumes (PostgreSQL data, Redis, etc.)
docker volume ls --filter "name=jarvis" -q | xargs -r docker volume rm

# 3. Remove the Docker network
docker network rm jarvis 2>/dev/null

# 4. Remove generated config files
rm -rf ~/.jarvis

# 5. (Optional) Remove pulled images to free disk space
docker images --filter "reference=ghcr.io/alexberardi/jarvis-*" -q | xargs -r docker rmi
docker images --filter "reference=postgres" -q | xargs -r docker rmi
docker images --filter "reference=redis" -q | xargs -r docker rmi
docker images --filter "reference=eclipse-mosquitto" -q | xargs -r docker rmi
docker images --filter "reference=grafana/*" -q | xargs -r docker rmi
```

!!! tip
    If you're reinstalling, you can skip step 5 — keeping the images avoids re-downloading them.

## Next Steps

- [Register a node and send your first command](first-command.md)
- [Understand configuration and network modes](configuration.md)
