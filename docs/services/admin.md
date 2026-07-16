# Admin

The admin service provides both a setup wizard for first-time installation and a web dashboard for ongoing management. It runs as a standalone binary (not a Python/FastAPI service) and manages all other Jarvis services via Docker.

## Quick Reference

| | |
|---|---|
| **Port** | 7711 (installer binary; on macOS this is also the permanent dashboard port — native only, never containerized) / 7710 (Docker container, Linux) |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-admin/` |
| **Framework** | Fastify (backend) + React (frontend), compiled with Bun |
| **Tier** | 5 - Clients |
| **Registry category** | Core (always installed) — since jarvis-admin#42 |
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
8. Downloads an LLM model, and optionally auto-fetches the Whisper speech-to-text model — see [macOS: Native Models Step](#macos-native-models-step-llm--whisper-auto-download)

### Admin Dashboard

After setup, the same binary serves the admin dashboard:

- **Dashboard** -- Container status overview, service health, LLM status
- **Services** -- Registered services, config/auth status, health checks
- **Models** -- Installed models, suggested downloads, custom HuggingFace downloads
- **Quick Sets** -- Named LLM configuration presets; apply or create to switch the active model without editing raw settings
- **Updates** -- Turn update checks on/off and run an update; see [Update Opt-In Toggle](#update-opt-in-toggle)
- **Settings** -- Runtime configuration across all services (proxied to config-service `/v1/settings/*`)
- **Nodes** -- Registered voice nodes

## Quick Sets

The **Quick Sets** page lets you create and apply named LLM configuration presets. A preset bundles a backend, model path, chat format, prompt provider, and context window into a single named profile that can be applied in one click.

### Model Path Dropdown

Added in jarvis-admin#6. The **Model file path** field on the apply panel now shows a dropdown of models installed on disk, populated from `GET /api/models/installed` (served by jarvis-llm-proxy-api). Values are `.models/<name>`-prefixed to match what the backend writes to `model.live.name` / `model.background.name`.

- When models are installed, the dropdown appears and pre-selects the current model if it matches an installed entry.
- Selecting **Other (custom path / HF ID)…** reveals the original free-text input for HuggingFace model IDs or paths not yet downloaded.
- When no models are installed the field falls back to free-text only.
- Freshly downloaded models appear in the dropdown without restarting admin — the endpoint scans `.models/` on each request.

## Sync Compose (Reconcile)

The **Sync Compose** page regenerates `docker-compose.yml`, `.env`, and `init-db.sh` from the current service registry + your selections, preserving existing secrets and settings. It offers two ways to apply the result:

- **Sync now** -- applies the regenerated files to the running stack in place (pull, apply, restart).
- **Download updated compose** (added in jarvis-admin#15) -- calls `POST /api/install/regenerate-download` and hands the operator the three regenerated files to download instead. Nothing on the server is touched. The operator drops the files in next to their existing compose and runs `docker compose up -d` by hand -- the review-first alternative for compose-managed installs that want to diff before applying.

`.env` merges new keys into existing values and `init-db.sh` covers any new databases, so replacing all three together (not just `docker-compose.yml`) is recommended even with the download path.

## Update Opt-In Toggle

Since jarvis-admin#54, the **Updates** page has a switch to turn update checks on/off — no more hand-editing a launchd plist (native macOS) or a compose `.env` and bootout/bootstrapping the service.

- `GET /api/update/settings` reads the current `allowUpdates` state; `POST /api/update/settings` (superuser only) persists it to `~/.jarvis/admin.json` and applies it to the live config immediately, with no restart required.
- Both `/check` routes return `updatesEnabled`, so the UI can tell "off, never checked" apart from "checked, you're current" — previously, checks being off silently rendered as "You're running the latest version."
- The `JARVIS_ALLOW_UPDATES` environment variable still works as a fallback (and remains the right knob for containerized installs); it is simply no longer the only way in. Default stays **off**: no outbound calls to GitHub unless you opt in. See [Network Egress & Offline Mode: Admin auto-update](../security/offline-mode.md#enabling-updates).

### Native Update Resume (Standalone Installs)

Since jarvis-admin#55, clicking Update on a standalone/native install (macOS) no longer leaves the upgrade stuck after the binary swap. The native upgrade path can't finish in one pass: `selfUpdate()` swaps the running binary and restarts the process, which kills the in-flight request and SSE stream mid-flight, so it writes `~/.jarvis/upgrade-in-progress.json` beforehand so the new binary can pick up where the old one died. Previously nothing on startup ever read that marker — the Update button swapped the admin binary and stopped: compose was never regenerated, images were never pulled, services never restarted, `installedVersion` in `admin.json` never advanced, and `/api/update/status` reported an upgrade permanently "in progress".

- A startup hook (`resumeUpgradeIfPending`) now reads the marker and finishes the job (compose regen → pull → restart → verify) when the marker's version matches the binary that's now running.
- It runs unawaited at startup — finishing the upgrade takes minutes (image pulls, container restarts), and the admin UI has to stay up throughout so the operator can watch `/api/update/status`.
- A marker written for a version that doesn't match the running binary (rollback, or a hand-installed binary) is discarded rather than resumed — regenerating compose for a version that isn't actually running would make things worse.
- A failed resume keeps the marker (`phase: "error"`) so the failure stays visible, but is not retried automatically on the next boot.
- `installedVersion` is only recorded once the resumed upgrade actually completes — not merely once the binary swap does.

On the client side, since jarvis-admin#56, the Updates page follows the *real* server-side upgrade instead of assuming it's done at the restart. Swapping the binary restarts the admin process, which kills the SSE stream mid-upgrade — the remaining work (compose regen → pull → restart → verify) used to be reported as instant success ("Upgrade complete!" with every phase ticked green) even while `docker compose pull` was still running on the box, because the phase list derives its checkmarks from the phase index and jumping straight to `done` retroactively marked every earlier phase complete. The page now polls `GET /api/update/status` until the server clears its upgrade marker, surfacing the real in-progress phase or a real failure instead of declaring victory early. The **Check for updates** toggle is also no longer hidden once an upgrade starts — it's a settings control, not an upgrade step, and previously disappeared for the rest of the session after running a single update.

## Architecture

```
jarvis-admin (Bun binary)
├── Server (Fastify)
│   ├── /api/auth/*          → Proxy to jarvis-auth
│   ├── /api/settings/*      → Proxy to config-service /v1/settings/*
│   ├── /api/install/*       → Setup wizard (generate, pull, start, register)
│   ├── /api/models/*        → Model management (list, download, delete, whisper-autodownload)
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

### Registry Category: Core (Always Installed)

Since jarvis-admin#42, jarvis-admin's own entry in `service-registry.json` moved from category `optional` to `core`. jarvis-admin is the management dashboard and the only interface for ongoing service management, but as `optional` it was default-off on the wizard's **Services** step — a fresh install could deselect it and end up with no way to manage the stack afterward. `core` services are pre-selected and cannot be deselected, so jarvis-admin is now guaranteed to be installed. The registry-category tests and the admin→command-center key test (previously "key only in optional block") were updated to match — the key guarantee is now "key only in the admin block, never leaked elsewhere."

### Production Hardening (JARVIS_ENV)

Since jarvis-admin#17, both `compose-generator.ts` and `env-generator.ts` opt every generated install into jarvis-auth's boot-time secret guard (see [jarvis-auth: secret guard](auth.md)):

- Every service and worker `environment:` block emits `JARVIS_ENV: "production"`.
- `env-generator.ts` never writes an empty `SECRET_KEY` — a missing value (e.g. reconstructing a gappy `.env`) is filled with a fresh strong secret (16 bytes for passwords, 32 for tokens/keys) instead of `""`, so a reconstructed install can't emit an empty secret under production enforcement.

This is safe by construction: admin's generators already produced strong secrets (no `"changeme"` fallback bug), so enabling the guard has nothing to trip on.

### MQTT Broker Lock (Fresh Installs)

Since jarvis-admin#27, `env-generator.ts` writes `MQTT_ALLOW_ANON=false` into every fresh install's `.env` — Mosquitto starts authenticated-only (`allow_anonymous false`) from first boot. A fresh install never needs the anonymous-broker window: command-center reads `MQTT_PASSWORD` from its own env, and every node fetches broker credentials over authenticated HTTP before it opens an MQTT connection (see [Command Center: MQTT Broker Auth](command-center.md#mqtt-broker-auth-transition)).

`compose-upgrader.ts` (used when regenerating `.env` for an existing install) preserves whatever value is already present. If the existing `.env` predates this change (no `MQTT_ALLOW_ANON` key at all), the upgrader explicitly writes `MQTT_ALLOW_ANON=true` — the transition window stays open for fleets that may still have un-migrated nodes, until the operator flips it. An explicit operator override always wins. Mirrors the installer SPA's export generator (see [Installer: MQTT Broker Lock](installer.md#mqtt-broker-lock-fresh-installs)).

### Command-Center Admin Key Wiring

Since jarvis-admin#31, the generator also emits `COMMAND_CENTER_ADMIN_KEY` (sourced from the shared `ADMIN_API_KEY` secret) into jarvis-admin's own container environment. The dashboard's **Nodes** train-adapter action and the Request Traces page authenticate to command-center's admin API (`/api/v0/admin/traces`, `/api/v0/nodes/{id}/commands`) with this key; it was previously never wired, so those calls silently sent an empty `X-API-Key` and command-center returned 401 once traces auth was enforced (jarvis-command-center#26).

Every route that proxies to a command-center admin endpoint now guards the key at request time: if `COMMAND_CENTER_ADMIN_KEY` is unset, the route fails loudly with `500` and a `COMMAND_CENTER_ADMIN_KEY is not configured` error instead of forwarding an empty key. See [Troubleshooting](#request-traces-or-node-actions-return-500-command_center_admin_key-is-not-configured).

### Update Stack to Latest (Download)

Since jarvis-admin#35, the Sync Compose / reconcile flow has an **"Update stack to latest"** button (`regenerateComposeFilesLatest()`, `POST /api/install/regenerate-download?latest=true`) that downloads a regenerated `docker-compose.yml` with image digests refreshed from GHCR — the newest published builds — rather than the frozen digest map baked into the admin binary at build time. Like the existing plain "Download updated compose" button, it never touches the running stack: the operator applies it themselves with `docker compose pull && docker compose up -d`. Because the operator applies it out-of-band, this is also the only way to update **jarvis-admin itself** — the in-place reconcile can't recreate the container it's running in. It's banner-independent (always available, not gated behind the release-driven Dashboard update banner). The default (no `latest` flag) path is unchanged config-only regeneration at the current pins.

The GHCR digest resolver (`refreshDigestsForTrack`) now resolves all tags concurrently rather than sequentially — the sequential version cost the *sum* of ~17 GHCR round-trips per refresh (seconds per upgrade, and it blew `compose-upgrader` unit-test timeouts under full-suite load). Each `resolveManifestDigest` call still self-contains its own error + timeout, so the concurrent `Promise.all` never rejects; a per-tag resolver failure just keeps the bundled digest.

### Supervised llm-proxy Launch (serve.sh)

Since jarvis-admin#34, the generated `llm-proxy` container's `command` is `["bash", "scripts/serve.sh"]` (the supervised launcher the image ships, added in jarvis-llm-proxy-api#21) rather than a raw unsupervised dual-uvicorn shell command. `serve.sh` runs the API server in the foreground and supervises the model service, respawning it with backoff on a native crash (e.g. a llama.cpp segfault) — previously a crashed model service was never restarted, and the API 503'd every request indefinitely while the container itself still looked healthy (the 2026-07-02 outage class, roadmap#59). Existing installs pick up the new command on their next compose regen/upgrade/reconcile, not immediately — a running stack keeps the old command until then.

### GPU Backend Persistence (Reconcile)

Since jarvis-admin#36, the reconcile (sync) flow persists Whisper's and TTS's GPU backend selections in `.env` and reads them back on every reconcile — fixing an incident class where a plain reconcile/regenerate silently reverted GPU configuration to CPU, because nothing had recorded the previous choice (prod 2026-07-04: whisper CUDA→CPU regressed STT from ~90ms to ~16s; prod 2026-07-06: a reconcile stripped TTS's GPU passthrough too, and the ReconcilePage selectors always reset to `cpu` since they never hydrated from the running install's options).

- **`WHISPER_BACKEND`** and **`TTS_BACKEND`** (+ **`TTS_GPU_DEVICE`** when `TTS_BACKEND=cuda`) are written to `.env` by `env-generator.ts` and read back by `state-reconstructor.ts` on every reconcile. An unrecognized or missing `WHISPER_BACKEND` value degrades to `cpu` rather than failing the reconcile.
- TTS GPU support is **device passthrough only** — the stock `jarvis-tts` image ships CUDA-capable Torch, so there's no `-cuda` image variant to select, unlike Whisper. The compose reservation pins a single GPU via `device_ids: ['${TTS_GPU_DEVICE:-0}']` (default `0`); using `count: all` OOM'd next to a 20GB LLM already on GPU0 in the 2026-07-05 incident.
- `GET /api/install/options` (consumed by the reconcile UI) now returns both `whisperBackend` and `ttsBackend`, and **ReconcilePage** hydrates its selectors from that response on load instead of defaulting to `cpu` every time the page opens.
- A new **Text-to-speech** section on the reconcile page lets operators switch the Kokoro TTS inference device (CPU default / NVIDIA CUDA), mirroring the existing Whisper GPU-backend selector (see [Whisper GPU Backend](installer.md#whisper-gpu-backend) for the underlying backend concept).
- See [TTS: Provider Selection](tts.md#provider-selection) for the Piper/Kokoro provider system this backend choice applies to.

### Floating Tags by Default (PIN_IMAGES Opt-In)

Since jarvis-admin#38 (2026-07-06 decision), image digest pinning is **opt-in** instead of the default: generated compose files use floating tags (`${JARVIS_IMAGE_TAG:-latest}<variant>`) for every image unless `PIN_IMAGES=true` is set in `.env`. Pinning-by-default meant `docker compose pull` could never actually update anything, and a stale bundled digest map could silently downgrade GPU-variant images back to CPU builds or pin `llm-proxy` to a build whose migration tree predated the database (the 2026-07-04/06 incidents) — a stuck non-expert operator had no supported way out short of a full regenerate.

- **`PIN_IMAGES`** (env var, default unset → `false`) — set to `true` to opt back into digest pinning, for supply-chain-hardened installs where a GHCR tag can be overwritten but a `@sha256` pin cannot.
- The `dev` release track always floats regardless of `PIN_IMAGES` (unchanged behavior, mirrors jarvis-installer#17 — dev exists to run the freshest CI-built images).
- **Migration is automatic**: a pre-existing install with a digest-pinned compose heals to floating tags on its next reconcile/regenerate, since a missing `PIN_IMAGES` key reconstructs as `false`. There is no separate migration step.
- The reconcile UI exposes this as a **"Pin images by digest"** checkbox (advanced, off by default) on the Sync Compose page.
- A new golden regression test (`prod-shape-regression.test.ts`, supersedes the jarvis-admin#37 draft) reconstructs wizard state from a prod-shaped `.env` and asserts GPU backends, broker credentials, and image pinning all regenerate correctly together in both the floating and `PIN_IMAGES=true` modes — covering the exact combination of settings the 2026-07-04/06 incidents broke at once.

### Notable Service Configurations

| Service | Notes |
|---------|-------|
| **command-center** | Runs `alembic upgrade head` before uvicorn; python-based health check (no curl in image); mounts `command-center-prompt-providers` volume at `/app/core/prompt_providers_custom` |
| **llm-proxy** | Launches via the supervised `scripts/serve.sh` entrypoint (see [Supervised llm-proxy Launch](#supervised-llm-proxy-launch-servesh)), which starts model service (7705) + API (7704) in one container; 120s health check start period. Emits `MODEL_SERVICE_TOKEN` (generated secret) on both the API and worker for internal auth to the model service — without it the model service 503s all inference while `/health` stays green (fixed in jarvis-admin#11, was previously missing from generated composes). On AMD GPUs also emits `JARVIS_FLASH_ATTN=false` (the gfx1201/RDNA4 HIP flash-attention kernel faults), matching the installer. Discrete-GPU device selection is handled in-image (see [LLM Proxy: Discrete-GPU Auto-Select](llm-proxy.md#discrete-gpu-auto-select-vulkan-rocm)), so the generator does not emit `*_VISIBLE_DEVICES`. |
| **whisper-api** | Since jarvis-admin#12, the sync generator selects Whisper's image variant + device passthrough from an **optional** `WizardState.whisperBackend` (`cpu` | `cuda` | `vulkan` | `rocm`, default `cpu` when unset) — independently of the LLM's auto-detected `gpuType`, mirroring the installer SPA's generator (see [Installer: Whisper GPU Backend](installer.md#whisper-gpu-backend)). Optional and defaulted so the upgrade state-reconstructor and older clients keep working with no fanout. Also wired end-to-end through the admin **reconcile (sync)** flow — a GPU-backend select on the Whisper section of ReconcilePage — so existing installs can switch Whisper's backend without a fresh install. Since jarvis-admin#36, this selection is persisted in `.env` (`WHISPER_BACKEND`) and read back on every reconcile, instead of silently reverting to `cpu` on regen (see [GPU Backend Persistence](#gpu-backend-persistence-reconcile)). |
| **tts** | Since jarvis-admin#36, the sync generator selects TTS's Kokoro inference **device** (CPU default / NVIDIA CUDA) from an optional `WizardState.ttsBackend`, persisted in `.env` (`TTS_BACKEND`, + `TTS_GPU_DEVICE` when `cuda`) and read back on reconcile — see [GPU Backend Persistence](#gpu-backend-persistence-reconcile). Unlike Whisper, this is device passthrough only; there's no separate `-cuda` image variant. |
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
| `MQTT_ALLOW_ANON` | Mosquitto `allow_anonymous` toggle written to `.env` by the generators (default: `false` on fresh install, `true` when upgrading a pre-existing `.env` that lacks the key). See [MQTT Broker Lock](#mqtt-broker-lock-fresh-installs). |
| `COMMAND_CENTER_ADMIN_KEY` | Admin API key used to authenticate to command-center's admin API (Request Traces, node train-adapter). Required; shares the `ADMIN_API_KEY` secret via `secretRef`. Emitted into jarvis-admin's own container since jarvis-admin#31 — see [Command-Center Admin Key Wiring](#command-center-admin-key-wiring). |
| `WHISPER_BACKEND` | Whisper's GPU backend (`cpu` \| `cuda` \| `vulkan` \| `rocm`, default `cpu`), written to the generated `.env` and read back on reconcile since jarvis-admin#36. See [GPU Backend Persistence](#gpu-backend-persistence-reconcile). |
| `TTS_BACKEND` | TTS's Kokoro inference device (`cpu` \| `cuda`, default `cpu`), written to the generated `.env` and read back on reconcile since jarvis-admin#36. See [GPU Backend Persistence](#gpu-backend-persistence-reconcile). |
| `TTS_GPU_DEVICE` | Which GPU index the `jarvis-tts` container reserves when `TTS_BACKEND=cuda` (default `0`). Re-pin when GPU0 is already full of LLM + Whisper. |
| `PIN_IMAGES` | Opt-in to digest-pinned images instead of floating tags (default unset → `false`). Since jarvis-admin#38 — see [Floating Tags by Default](#floating-tags-by-default-pin_images-opt-in). |
| `HUGGINGFACE_HUB_TOKEN` | Persisted to `~/.jarvis/compose/.env` when a HuggingFace token is supplied during the Models step's LLM download, so gated repos can still be pulled at service runtime. Since jarvis-admin#49 — see [macOS: Native Model Downloads via curl](#macos-native-model-downloads-via-curl-no-venv). |
| `JARVIS_ALLOW_UPDATES` | Fallback/container knob for the [Update Opt-In Toggle](#update-opt-in-toggle) — same effect as flipping the switch on the Updates page, without a UI. |

## Dependencies

- **Docker** -- manages all Jarvis service containers
- **jarvis-config-service** -- service discovery and registration
- **jarvis-auth** -- user authentication, app-to-app credential creation
- **jarvis-config-service** -- settings gateway (`/v1/settings/*`) behind the admin Settings page

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

## macOS: Native Binary Persists After Install

Since jarvis-admin#44, on macOS the native admin binary does **not** self-terminate after a successful install. Previously the install-completion handler assumed a *containerized* admin would take over the dashboard port and always killed itself (`disableAutostart()` + `process.exit(0)`) — but macOS never containerizes admin (see [Installation: Platform Notes](../getting-started/installation.md#macos-apple-silicon)), so the dashboard and the native-services install step that follows lost their backend entirely.

On macOS the native binary now:

- Stays alive after install and serves the full dashboard app itself (instead of redirecting to a container port nothing listens on).
- Keeps the same port throughout — the CLI success message reads "your admin dashboard stays at the same `http://localhost:7711`" rather than pointing at a different post-install port.

This only affects macOS. On Linux, the native installer binary still hands off to the containerized admin on port 7710 and self-terminates as before.

## macOS: Native Models Step (LLM + Whisper Auto-Download)

Since jarvis-admin#46, the wizard's **LLM** step is now the **Models** step and works on native macOS installs — previously it bailed out entirely on `darwin`, telling the operator to configure the LLM proxy manually after setup.

- **LLM download**: `POST /api/models/download` now finds/creates a native `.models` dir at `~/.jarvis/native/jarvis-llm-proxy-api/.models` (falling back through the existing Docker-oriented candidates when that checkout isn't present), and runs the Python download script with the native llm-proxy venv's Python (`~/.jarvis/native/jarvis-llm-proxy-api/.venv/bin/python`, which has `huggingface_hub`) instead of a bare `python3` — the macOS system Python is 3.9 and lacks the package.
- **vLLM hidden on macOS**: it's Linux+CUDA only; the wizard's backend toggle only shows GGUF natively.
- **Whisper auto-download**: a **`POST /api/models/whisper-autodownload`** endpoint (added in jarvis-admin#48) upserts `WHISPER_ALLOW_MODEL_AUTODOWNLOAD` into `~/.jarvis/compose/.env` — the fallback whisper reads even while its own settings DB is unreachable (e.g. crash-looping on a missing model) — then best-effort `launchctl kickstart`s the native whisper service so it fetches `ggml-base.en` on the next load.
- **Apply order**: the LLM download + configure runs first and must succeed; the Whisper auto-download step runs after and is best-effort — a Whisper hiccup does not undo an already-applied LLM (jarvis-admin#48 fixed an earlier ordering bug where a transient Whisper 500 aborted the flow before the LLM download ran at all).
- **Native restarts**: on macOS, applying the LLM config kickstarts the native `jarvis-llm-proxy-api` launchd job to reload with the new model; a failed kickstart is logged and left to the plist's `KeepAlive` to retry rather than failing the wizard.
- **Wizard flow**: the post-install redirect (which normally sends the browser to the containerized admin's dashboard) is skipped on macOS (jarvis-admin#47) — there's no container to hand off to, and redirecting reloaded the native app into a path that skipped the Account and Models steps. The wizard now stays in-session: Install → Account → Models → Finish.

## macOS: Native Model Downloads via curl (No venv)

The setup wizard's Models step (formerly the LLM step) was extended to work on native macOS installs in jarvis-admin#46, and its same-day follow-ups #47/#48 fixed the wizard actually reaching that step and reordered its apply sequence (LLM first, Whisper best-effort after) — see the separate doc PR covering that batch.

jarvis-admin#49 and #50 fixed the download path itself for a real-world field failure ("Download failed: 500"): the native `jarvis-llm-proxy-api` builds its Python venv asynchronously after install, so it usually isn't up — or its venv `huggingface_hub` isn't installed yet — when the Models step actually runs.

- **LLM GGUF download (#49)** — single-file GGUF downloads now go straight through `curl` (the HuggingFace resolve URL, with an `Authorization: Bearer` header when a token is supplied) instead of shelling out to the llm-proxy venv's Python. Full-repo snapshots (no explicit filename — used by the vLLM backend) still require the local venv python and `huggingface_hub`.
- **Model configuration persisted to `.env` (#49)** — `POST /api/llm-setup/configure` now writes `JARVIS_MODEL_NAME`, `JARVIS_MODEL_BACKEND`, `JARVIS_MODEL_CHAT_FORMAT`, and `JARVIS_MODEL_CONTEXT_WINDOW` into `~/.jarvis/compose/.env` on darwin *before* attempting the HTTP settings write. llm-proxy's settings seed reads these as env-fallbacks on first start, so the chosen model sticks even if llm-proxy isn't reachable yet — a non-200 from the HTTP write no longer fails the request on darwin.
- **Whisper STT model (#50)** — `POST /api/models/whisper-autodownload` no longer relies solely on setting `WHISPER_ALLOW_MODEL_AUTODOWNLOAD` and restarting whisper to trigger its own download. Whisper's autodownload gate reads a DB-backed setting (not the env var), and that settings table doesn't exist until the service is up natively — so the endpoint now `curl`s `ggml-base.en.bin` (~148 MB, from `ggerganov/whisper.cpp`) straight to whisper's default model path, and whisper simply finds the file locally on next start. The env var is still written for completeness, and the native service is still best-effort kickstarted (`launchctl kickstart -k`) afterward — a kickstart failure doesn't fail the request; launchd's `KeepAlive` restarts the service anyway.

A HuggingFace token supplied during the LLM download is persisted to `HUGGINGFACE_HUB_TOKEN` in `.env` so gated models keep working on subsequent runtime pulls, not just the initial wizard download.

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

### Request Traces or node actions return 500 `COMMAND_CENTER_ADMIN_KEY is not configured`

Since jarvis-admin#31, the Request Traces page and the Nodes train-adapter action fail loudly with a `500` instead of a confusing `401` when `COMMAND_CENTER_ADMIN_KEY` is missing from the admin container's environment. Regenerate `.env` (or re-run the setup wizard) so the generator wires the key from the shared `ADMIN_API_KEY` secret — see [Command-Center Admin Key Wiring](#command-center-admin-key-wiring).

### macOS: "Docker not found" even though Docker Desktop is running

A launchd-started admin (the default auto-start method on macOS) inherits launchd's minimal `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`), which excludes the paths Docker Desktop installs its CLI to (`/opt/homebrew/bin`, `/usr/local/bin`, or the app bundle). Every `execSync('docker ...')` then failed with "command not found", so the install wizard reported "Docker not found" even with Docker Desktop actually running.

Since jarvis-admin#40, `ensureDockerOnPath()` runs at startup and prepends the standard Docker Desktop bin locations to `PATH` (only ones that exist, never duplicating), independent of how the admin was launched. The generated launchd plist also now sets `PATH` in `EnvironmentVariables` as a second layer of defense. If you still see this error after upgrading, restart the admin service so the regenerated plist takes effect:

```bash
launchctl unload ~/Library/LaunchAgents/com.jarvis.admin.plist
launchctl load ~/Library/LaunchAgents/com.jarvis.admin.plist
```

### macOS install stalls with only config + auth running

On macOS, `whisper-api` and `llm-proxy` run natively (excluded from the generated compose so they can reach Metal — see [Platform Notes](../getting-started/installation.md#macos-apple-silicon)), but the wizard's `tieredStartup` step still passed their service names to `docker compose up -d ...`. Docker validates every service name up front and aborts the *entire* batch on the first `no such service: jarvis-whisper-api`, so the install stalled after config-service and auth came up healthy and nothing else ever started.

Since jarvis-admin#41, the wizard introspects the generated compose (`docker compose config --services`) before starting the remaining services and only `up`s services that are actually defined in it (`selectRemainingToStart()`). If the introspection call itself fails, the wizard falls back to the unfiltered list rather than blocking the install.

### Update stuck reporting "in progress" after a standalone Update

Since jarvis-admin#55, this resolves itself on the next admin restart: a startup hook resumes any interrupted upgrade whose marker matches the running binary version. If it's still stuck after a restart, check the logs for `upgrade resume failed` — the marker (`~/.jarvis/upgrade-in-progress.json`) is kept with `phase: "error"` on failure rather than retried automatically, so clearing it by hand is the way to force a clean retry. See [Native Update Resume](#native-update-resume-standalone-installs).
