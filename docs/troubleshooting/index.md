# Troubleshooting

Quick fixes for common Jarvis issues. If your problem is not listed here, check the [Getting Help](#getting-help) section at the bottom.

## Installation Issues

### Docker not found

**Symptom:** `docker: command not found` when running the installer.

**Fix:** Install Docker for your platform. See the [Prerequisites](../getting-started/installation.md#prerequisites) section of the installation guide for full commands.

```bash
# Verify Docker is installed
docker --version
```

### Docker Compose missing

**Symptom:** `docker compose` returns `docker: 'compose' is not a docker command`.

Docker Compose v2 ships as a Docker CLI plugin. If it is missing, install it manually:

=== "Ubuntu / Debian"

    ```bash
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    ```

=== "TrueNAS SCALE"

    TrueNAS locks `apt`, so install the binary directly:

    ```bash
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
    ```

=== "macOS"

    Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), which bundles Compose v2.

Verify after installing:

```bash
docker compose version
```

### Port already in use

**Symptom:** Container exits immediately with `Bind for 0.0.0.0:<port> failed: port is already allocated`.

Find what is using the port and stop it:

=== "macOS / Linux"

    ```bash
    # Check what is using port 7703, for example
    lsof -i :7703
    ```

=== "Linux (alternative)"

    ```bash
    ss -tlnp | grep 7703
    ```

Common conflicts:

| Port | Jarvis Service | Common Conflict |
|------|---------------|-----------------|
| 5432 | PostgreSQL | Existing PostgreSQL install |
| 6379 | Redis | Existing Redis install |
| 9000 | MinIO | MinIO or other S3-compatible tools |

**Fix:** Stop the conflicting process, or change the Jarvis port in `~/.jarvis/compose/.env`.

### Docker socket permission denied

**Symptom:** `Got permission denied while trying to connect to the Docker daemon socket`.

**Fix:** Add your user to the `docker` group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Log out and back in for the group change to take full effect.

!!! note
    On macOS with Docker Desktop, this error usually means Docker Desktop is not running. Open it from Applications.

### Image pull failures

**Symptom:** `Error response from daemon: pull access denied` or timeout errors during install.

Possible causes:

1. **No internet access** -- Check your network connection.
2. **GHCR rate limit** -- GitHub Container Registry has rate limits for unauthenticated pulls. Authenticate:
    ```bash
    echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
    ```
3. **Proxy settings** -- If you are behind a corporate proxy, configure Docker:
    ```bash
    # Create or edit ~/.docker/config.json
    {
      "proxies": {
        "default": {
          "httpProxy": "http://proxy:8080",
          "httpsProxy": "http://proxy:8080"
        }
      }
    }
    ```

### Slow service startup

Some services take longer to start than others. Expected startup times:

| Service | Typical Startup |
|---------|----------------|
| PostgreSQL, Redis | 2-5 seconds |
| Config Service, Auth, Logs | 3-10 seconds |
| Command Center | 10-30 seconds (runs Alembic migrations) |
| LLM Proxy | 30-120 seconds (loads model into memory) |

If a service seems stuck, check its logs:

```bash
cd ~/.jarvis/compose && docker compose logs <service-name> --tail 50
```

!!! tip
    The LLM Proxy has a 120-second health check start period. The admin dashboard may show it as "starting" for up to two minutes while the model loads.

## Service Health Issues

### "Connection refused" errors

**Symptom:** `ECONNREFUSED` or `Connection refused` when a service tries to reach another.

**Checklist:**

1. Is the target service running?
    ```bash
    cd ~/.jarvis/compose && docker compose ps
    ```
2. Is it on the right port? Check `~/.jarvis/compose/.env` for port assignments.
3. Are both services on the same Docker network?
    ```bash
    docker network inspect jarvis
    ```

### Service shows unhealthy in admin dashboard

Check the service logs for the specific error:

```bash
cd ~/.jarvis/compose && docker compose logs <service-name> --tail 100
```

Common causes by service:

| Service | Common Cause | Fix |
|---------|-------------|-----|
| Config Service | PostgreSQL not ready | Wait for PostgreSQL to start, check `DATABASE_URL` |
| Auth | Database migration failed | Check PostgreSQL logs, verify connection string |
| Command Center | LLM Proxy unreachable | Start LLM Proxy first, check `LLM_PROXY_URL` |
| LLM Proxy | No model loaded | Download a model via the admin dashboard Models page |
| TTS | Piper model missing | Download a Piper voice model to `app/models/` |
| TTS | Kokoro weights slow to download | Mount `jarvis-tts-hf-cache` volume so weights persist across restarts |
| TTS | Selected provider failed to load | Service falls back to Piper and logs a warning; check `tts.provider` and provider extras are installed |

### Database migration failures

**Symptom:** Service logs show `alembic` errors or `relation does not exist`.

**Causes:**

1. PostgreSQL not ready yet -- the service started before PostgreSQL accepted connections.
2. Wrong `DATABASE_URL` -- check the connection string in the service's environment.

**Fix:** Restart the failing service. Docker Compose health checks should handle startup ordering, but a manual restart resolves most timing issues:

```bash
cd ~/.jarvis/compose && docker compose restart <service-name>
```

If the issue persists, check that the database exists:

```bash
docker exec jarvis-postgres psql -U postgres -l
```

### Authentication failures

**Symptom:** `401 Unauthorized` from service-to-service calls.

**Possible causes:**

- **App-to-app keys missing:** The service is not registered in config-service, or its `JARVIS_APP_ID` and `JARVIS_APP_KEY` environment variables are wrong.
- **JWT expired:** User tokens expire. Log in again to get a fresh token.
- **Admin token mismatch:** The `ADMIN_API_KEY` in the command center does not match what you are sending.

**Fix:** Re-run the installer's registration step, or check `~/.jarvis/compose/.env` for the correct credentials.

### Config service unreachable

All services depend on config-service for discovery. If config-service is down, other services will fail to start or lose the ability to find each other.

**Check config-service first:**

```bash
curl -s http://localhost:7700/health
```

If it is not responding:

```bash
cd ~/.jarvis/compose && docker compose logs jarvis-config-service --tail 50
```

The most common cause is PostgreSQL not being ready. Check PostgreSQL:

```bash
docker exec jarvis-postgres pg_isready -U postgres
```

## Node Issues

### Node cannot connect to command center

**Symptom:** Node logs show connection errors to port 7703.

**Checklist:**

1. Is the command center running?
    ```bash
    curl -s http://localhost:7703/health
    ```
2. Is the node's API key correct? Compare `node_id` and `api_key` in the node's config file against what is registered in the command center.
3. Is the command center reachable from the node's network? If the node is on a different machine, use the server's IP address, not `localhost`.
4. Check firewall rules -- port 7703 must be open for inbound TCP.

### MQTT connection lost

**Symptom:** Node logs show `MQTT broker not reachable` or repeated reconnection attempts.

**Check the Mosquitto container:**

```bash
docker ps | grep mosquitto
```

If it is not running, restart it:

```bash
cd ~/.jarvis/compose && docker compose up -d mosquitto
```

The default MQTT broker port is **1883** (internal) / **1884** (external). Verify the node's MQTT config points to the correct host and port.

### Commands not available after install

**Symptom:** You installed a Pantry package, but the command does not work.

The command center caches available tools. After installing a package on a node:

1. Wait up to 10 minutes for the discovery refresh cycle.
2. Or restart the node container to force an immediate refresh:
    ```bash
    docker restart <node-container>
    ```

Check that the node reports the new command:

```bash
docker logs <node-container> 2>&1 | grep -i "discovery"
```

### Voice not responding

**Symptom:** Wake word detected but no response, or no wake word detection at all.

**Checklist:**

1. **Microphone:** Check that the correct audio input device is configured. Look for PyAudio errors in node logs.
2. **Wake word:** Verify the Porcupine wake word model is loaded (check node config for `wake_word` settings).
3. **Whisper API:** If the node sends audio to Whisper for transcription, verify Whisper is running:
    ```bash
    curl -s http://localhost:7706/health
    ```
4. **TTS:** If voice responses are expected, check that TTS is running:
    ```bash
    curl -s http://localhost:7707/health
    ```

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `ECONNREFUSED 127.0.0.1:7700` | Config service not running | Start config-service first |
| `401 Unauthorized` | Invalid API key or expired token | Re-register node or refresh token |
| `pg_isready: connection refused` | PostgreSQL still starting | Wait 10-15 seconds, then retry |
| `MQTT broker not reachable` | Mosquitto container down | `cd ~/.jarvis/compose && docker compose up -d mosquitto` |
| `No model loaded` | LLM Proxy has no model | Download a model via admin dashboard Models page |
| `Bind for 0.0.0.0:PORT failed` | Port already in use | Find and stop the conflicting process (see [Port already in use](#port-already-in-use)) |
| `permission denied` on Docker socket | User not in docker group | `sudo usermod -aG docker $USER && newgrp docker` |
| `relation "..." does not exist` | Database migration not run | Restart the service to re-run Alembic migrations |

## Getting Help

If your issue is not listed here:

1. **Check service logs:**
    ```bash
    cd ~/.jarvis/compose && docker compose logs <service-name> --tail 100
    ```
2. **Check the admin dashboard** at [http://localhost:7711](http://localhost:7711) -- the Dashboard page shows container status and service health.
3. **Use the CLI health check** (source installs):
    ```bash
    ./jarvis health
    ```
4. **Open an issue** on [GitHub](https://github.com/alexberardi/jarvis/issues) with:
    - Your platform (macOS/Linux/TrueNAS)
    - The output of `docker compose ps`
    - Relevant service logs
