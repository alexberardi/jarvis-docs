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

## Service Registry

Service definitions live in `public/service-registry.json`. Each entry defines the Docker image, configurable ports, required environment variables, and named volumes. Two generators consume this file:

- **`compose-generator.ts`** — powers the interactive UI selection list
- **`compose-export-generator.ts`** — produces the static compose file for download

Both generators treat infrastructure images (postgres, Redis, etc.) as fixed — `JARVIS_IMAGE_TAG` and release-track overrides are not applied to them.

## vs. Admin Wizard

Both the installer SPA and the `jarvis-admin` setup wizard generate Docker Compose stacks, but serve different use cases:

| | Installer SPA | Admin Setup Wizard |
|---|---|---|
| **Requires install** | No — runs in any browser | Yes — admin binary (`~7 MB`) |
| **Executes compose** | No — download only | Yes — pulls images and starts services |
| **Ongoing management** | No | Yes — dashboard, model downloads, settings |
| **Good for** | Scripted deploys, air-gapped prep | Interactive first-time setup |

For most installs, use the **admin wizard** via `curl … | sh` or `npx @alexberardi/jarvis-admin` — it handles the full install lifecycle interactively. Use the installer SPA when you need a compose file without running the admin binary first.
