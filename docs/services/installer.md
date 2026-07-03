# Installer

The Jarvis Installer is a static React SPA that generates a Docker Compose stack for initial deployment. It runs entirely in the browser without a backend and produces a downloadable `docker-compose.yml` configured for the services you select.

## Quick Reference

| | |
|---|---|
| **Source** | `jarvis-installer/` |
| **Framework** | React (static SPA) |
| **Output** | Downloadable `docker-compose.yml` |
| **Use case** | Compose file generation without installing the admin binary |

## Infrastructure Images

The installer generates compose files with fixed infrastructure images. These images are not tagged with `JARVIS_IMAGE_TAG` or release tracks — infra images are pinned independently of the Jarvis service release cycle.

| Service | Image | Notes |
|---------|-------|-------|
| PostgreSQL | `pgvector/pgvector:pg16` | Required — see below |

### PostgreSQL: pgvector Required

The installer uses `pgvector/pgvector:pg16` rather than stock `postgres:16` or `postgres:16-alpine`. Stock postgres does not ship the `vector` extension. Command-center's alembic migration `e9f0a1b2c3d4` (`add_embedding_and_pinned_to_memories`) runs `CREATE EXTENSION IF NOT EXISTS vector` and will abort with:

```
extension "vector" does not exist
```

if the postgres image does not include pgvector. `pgvector/pgvector:pg16` is the official drop-in for `postgres:16`.

!!! warning "Do not swap the postgres image"
    Replacing `pgvector/pgvector:pg16` with `postgres:16` or `postgres:16-alpine` in installer-generated compose files causes `jarvis-command-center` to fail at startup.

## Whisper GPU Backend

Since jarvis-installer#8, `WizardState.whisperBackend` (`cpu` | `cuda` | `vulkan` | `rocm`, default **cpu**) lets you pick Whisper's GPU backend **independently** of the LLM's auto-detected `gpuType`. Previously Whisper's image variant just followed the LLM's GPU type, and AMD/Vulkan boxes were hardcoded to CPU.

| Backend | Image suffix | Device passthrough |
|---------|--------------|---------------------|
| `cpu` (default) | none | none |
| `cuda` | `-cuda` | NVIDIA deploy block |
| `vulkan` | `-vulkan` | `/dev/dri` + render group |
| `rocm` | `-rocm` | `/dev/dri` + `/dev/kfd` |

Default `cpu` keeps Whisper off the GPU — `base.en` is fast enough on CPU, leaving the GPU free for the LLM.

Both generators implement this via a whisper-scoped image lookup + a whisper-aware GPU config helper:

- **`compose-export-generator.ts`** (downloadable file) — since #8.
- **`compose-generator.ts`** (interactive preview) — since jarvis-installer#10, for full parity with the export path and the admin sync generator.

Since jarvis-installer#9, the **Configuration** step surfaces a `whisperBackend` selector (CPU default / NVIDIA CUDA / AMD Vulkan / AMD ROCm) next to the Whisper model picker, dispatching `SET_WHISPER_BACKEND`. Default `cpu` means zero behavior change for existing installs — this is opt-in GPU-accelerated speech-to-text.

## Generated Secrets

The installer mints a fresh, random secret for every sensitive credential in `SECRET_KEYS` (`src/lib/secret-generator.ts`) rather than shipping fixed defaults — this includes database passwords, `ADMIN_API_KEY`, and `GRAFANA_ADMIN_PASSWORD` (the Grafana container's `GF_SECURITY_ADMIN_PASSWORD`). Earlier installer versions hardcoded the Grafana admin password to the literal `jarvis`; it's now generated per-install like the other secrets and baked into the exported compose file.

### Compose Export: Consistent Strong Secrets + Production Mode

Since jarvis-installer#12, the downloadable `compose-export-generator.ts` path resolves every secret **once** via a memoized `resolveSecret()` and reuses that same value everywhere it's referenced: a wizard-provided value wins, otherwise a strong random secret is generated. This fixes a mismatch where the export's `SecretsMap` fell back to the literal `"changeme"` while the generic per-service env loop fell back to `""` for the same secret ref — producing different values for what should be one shared secret (e.g. `AUTH_SECRET_KEY`) and silently breaking fleet-wide JWT validation on a partial-wizard export. `"changeme"` is also on jarvis-auth's boot-time secret guard blocklist (see [jarvis-auth: secret guard](auth.md)), so a prod export using it was a latent boot-breaker.

The export also now emits `JARVIS_ENV: "production"` on every service, opting a fresh install into that boot-time secret enforcement. This is safe by construction — the export always bakes strong, consistent secrets, so the guard has nothing to trip on.

## Service Registry

Service definitions live in `public/service-registry.json`. Each entry defines the Docker image, configurable ports, required environment variables, and named volumes. Two generators consume this file:

- **`compose-generator.ts`** — powers the interactive UI selection list
- **`compose-export-generator.ts`** — produces the static compose file for download

Both generators treat infrastructure images (postgres, Redis, etc.) as fixed — `JARVIS_IMAGE_TAG` and release-track overrides are not applied to them.

### Named Volumes

The exported `docker-compose.yml` includes a top-level `volumes:` block declaring the two app-level named volumes. Without this declaration Docker Compose rejects the file at startup with `invalid compose project`.

| Volume | Used by service |
|--------|----------------|
| `whisper-voice-profiles` | `jarvis-whisper-api` |
| `command-center-prompt-providers` | `jarvis-command-center` |

Infrastructure services (postgres, Redis, Mosquitto) use bind mounts rather than named volumes and are not listed here.

Both `compose-generator.ts` (interactive preview) and `compose-export-generator.ts` (download) apply the same top-level volume declarations.

## vs. Admin Wizard

Both the installer SPA and the `jarvis-admin` setup wizard generate Docker Compose stacks, but serve different use cases:

| | Installer SPA | Admin Setup Wizard |
|---|---|---|
| **Requires install** | No — runs in any browser | Yes — admin binary (~7 MB) |
| **Executes compose** | No — download only | Yes — pulls images and starts services |
| **Ongoing management** | No | Yes — dashboard, model downloads, settings |
| **Good for** | Scripted deploys, air-gapped prep | Interactive first-time setup |

For most installs, use the **admin wizard** via `curl … | sh` or `npx @alexberardi/jarvis-admin` — it handles the full install lifecycle interactively. Use the installer SPA when you need a compose file without running the admin binary first.
