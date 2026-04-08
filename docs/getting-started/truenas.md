# TrueNAS Setup

Step-by-step guide for installing Jarvis on TrueNAS SCALE.

## Requirements

- TrueNAS SCALE 24.10 (Electric Eel) or newer
- SSH access to your NAS
- Docker (included with TrueNAS SCALE 24.10+)

!!! warning "Do not use the TrueNAS Apps UI"
    The TrueNAS Apps catalog runs containers in a sandboxed environment without access to the Docker socket. Jarvis needs socket access to create and manage its service containers. Always install via the SSH terminal.

!!! danger "Older TrueNAS SCALE versions are not supported"
    TrueNAS SCALE versions before 24.10 (Dragonfish, Cobia) use k3s instead of Docker. Upgrade to Electric Eel or later, or run Jarvis in a VM.

## Step 1: Verify Docker

SSH into your TrueNAS server and confirm Docker is available:

```bash
ssh root@<your-nas-ip>

# Check Docker
docker info

# Check Compose
docker compose version
```

If `docker compose` is not found, install the Compose plugin manually. TrueNAS locks `apt`, so you need to install the binary directly:

```bash
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p "$DOCKER_CONFIG/cli-plugins"
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"

# Verify
docker compose version
```

## Step 2: Install Jarvis

Run the installer container via Docker. This starts the admin panel with the setup wizard:

```bash
docker run -d \
  --name jarvis-admin \
  -p 7711:7711 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/alexberardi/jarvis-admin:latest
```

!!! note "Docker socket path"
    The default socket path is `/var/run/docker.sock`. If your TrueNAS installation uses a different path, verify it with `ls -la /var/run/docker.sock` and adjust the `-v` mount accordingly. You can also set the `DOCKER_SOCKET` environment variable (see [Docker Socket Location](#docker-socket-location)).

Open the setup wizard in your browser:

```
http://<your-nas-ip>:7711
```

## Step 3: Run the Setup Wizard

The setup wizard works the same as on any other platform. Walk through the seven steps:

1. **Welcome** -- system check
2. **Hardware** -- detects platform and RAM
3. **Services** -- select which services to enable
4. **Review** -- confirm configuration
5. **Install** -- generates Docker Compose, pulls images, starts services
6. **Account** -- create your superuser account
7. **LLM** -- select and download a language model

!!! tip "LLM model selection on TrueNAS"
    TrueNAS servers typically lack a dedicated GPU. Select a smaller model (Qwen 3 4B or Qwen 3 8B) for CPU inference, or configure a remote LLM endpoint if you have a separate GPU server.

## Step 4: Auto-Start on Boot

TrueNAS does not support user-level systemd services (`systemctl --user`). Use one of these alternatives to ensure Jarvis starts after a reboot.

### Option A: TrueNAS Init/Shutdown Script

TrueNAS SCALE provides an init/shutdown script feature in the web UI:

1. Go to **System > Advanced > Init/Shutdown Scripts** in the TrueNAS web UI.
2. Click **Add**.
3. Configure:
    - **Description:** `Start Jarvis`
    - **Type:** `Command`
    - **Command:**
      ```
      docker start jarvis-admin && cd /root/.jarvis/compose && docker compose up -d
      ```
    - **When:** `Post Init`
4. Save.

### Option B: Cron @reboot Entry

Add a `@reboot` cron job:

```bash
crontab -e
```

Add this line:

```
@reboot sleep 30 && docker start jarvis-admin && cd /root/.jarvis/compose && docker compose up -d
```

The 30-second delay gives Docker time to initialize after boot.

!!! tip
    Option A is preferred because it integrates with TrueNAS's own startup sequence and is visible in the web UI.

## Docker Socket Location

The default Docker socket path is `/var/run/docker.sock`. Verify it exists:

```bash
ls -la /var/run/docker.sock
```

If your socket is in a different location, tell the admin container where to find it:

```bash
docker run -d \
  --name jarvis-admin \
  -p 7711:7711 \
  -e DOCKER_SOCKET=/path/to/docker.sock \
  -v /path/to/docker.sock:/var/run/docker.sock \
  ghcr.io/alexberardi/jarvis-admin:latest
```

## Data Storage

Jarvis stores its configuration and generated files in `~/.jarvis/`:

| Path | Contents |
|------|----------|
| `~/.jarvis/compose/` | Generated `docker-compose.yml`, `.env`, database init scripts |
| `~/.jarvis/compose/.models/` | Downloaded LLM model files (can be several GB each) |
| `~/.jarvis/admin.json` | Admin panel configuration |

PostgreSQL data is stored in a Docker volume (`jarvis-postgres-data`). To see its location on disk:

```bash
docker volume inspect jarvis-postgres-data
```

### Backup Recommendations

- **Config files:** Back up `~/.jarvis/` to preserve your configuration and credentials.
- **PostgreSQL data:** Use `pg_dump` for portable database backups:
    ```bash
    docker exec jarvis-postgres pg_dumpall -U postgres > jarvis-backup.sql
    ```
- **Models:** LLM models can be re-downloaded, but backing them up avoids large downloads after a restore.

!!! tip
    If your TrueNAS datasets are already part of a ZFS snapshot schedule, ensure the Docker volumes and `~/.jarvis/` directory are on a snapshotted dataset.

## Known Limitations

- **No `apt`** -- TrueNAS locks the system package manager. You cannot install packages directly. Use Docker containers for any additional tools.
- **No GPU passthrough** -- TrueNAS SCALE does not support GPU passthrough to Docker containers. Use CPU inference (smaller models) or configure a remote LLM endpoint on a machine with a GPU.
- **LLM model downloads** -- Download models through the admin dashboard Models page or manually place files in `~/.jarvis/compose/.models/`.
- **No user-level systemd** -- Use init scripts or cron for auto-start (see [Step 4](#step-4-auto-start-on-boot)).

## Troubleshooting

### Previous TrueNAS App installation left behind

If you previously installed Jarvis through the TrueNAS Apps UI, remove it from the Apps page first, then clean up Docker resources:

```bash
# Remove leftover containers
docker ps -a --filter "name=jarvis" -q | xargs -r docker rm -f

# Remove leftover volumes
docker volume ls --filter "name=jarvis" -q | xargs -r docker volume rm

# Remove leftover network
docker network rm jarvis 2>/dev/null
```

Then proceed with [Step 2](#step-2-install-jarvis).

### Docker socket permission denied

If the installer reports socket access errors:

```bash
# Check socket permissions
ls -la /var/run/docker.sock

# If running as non-root, add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker
```

On TrueNAS, you are typically logged in as root via SSH, so socket permissions are rarely an issue.

### Services cannot reach each other

Services communicate via `host.docker.internal`. Verify it resolves correctly from inside a container:

```bash
docker exec jarvis-config-service ping -c 1 host.docker.internal
```

If it does not resolve, check that your Docker version supports `host.docker.internal` on Linux (Docker 20.10+).

### Compose file not found after reboot

If `docker compose up -d` fails after a reboot with "no configuration file found", verify the compose directory exists:

```bash
ls -la ~/.jarvis/compose/docker-compose.yml
```

If the file is missing, the initial setup may not have completed. Re-run the installer (see [Step 2](#step-2-install-jarvis)).

For more issues, see the [Troubleshooting](../troubleshooting/index.md) guide.
