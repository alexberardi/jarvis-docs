# Pantry Store

The Pantry Store is the server-side API for the Jarvis Pantry — the package registry and submission pipeline for community-built commands. It manages submissions, dispatches test runs to GitHub Actions, verifies results via signed callbacks, and publishes approved packages.

## Quick Reference

| | |
|---|---|
| **Deployment** | Fly.io (`jarvis-pantry-store`) |
| **Source** | `jarvis-pantry/` |
| **Framework** | FastAPI + SQLAlchemy |
| **Database** | PostgreSQL (Fly managed) |
| **Health endpoint** | `GET /health` |

## Submission Pipeline

1. **Submit** — Developer POSTs a manifest + package URL via the Pantry web UI or CLI
2. **Resolve** — Pantry resolves a pip dependency lockfile for the submission's declared packages
3. **Dispatch** — Pantry triggers a `workflow_dispatch` on `jarvis-pantry-runner` with `submission_id`, `nonce`, and the resolved lockfile as inputs
4. **Run** — The runner's two-job workflow tests the submission in an isolated Docker sandbox
5. **Callback** — Runner POSTs a signed result to `/v1/submissions/{id}/container-result`
6. **Verify** — Pantry verifies the HMAC signature and updates submission state to `published` or `rejected`

## Callback Security Model

Container test results are verified using **HMAC-SHA256** over the raw request body, keyed by `PANTRY_CALLBACK_SIGNING_KEY`.

### How It Works

The runner signs over `{submission_id}|{nonce}|{request_body_bytes}` and sends the digest in the `X-Pantry-HMAC` header. Pantry recomputes the digest from the raw `request.body()` bytes (not from a parsed JSON object) so the digest covers exactly the bytes that will be sent on the wire.

The `nonce` is a per-submission random value Pantry generates at dispatch time and stores in the database. It prevents replay attacks — a captured callback payload cannot be replayed against a different submission.

### Startup Guard

When `PANTRY_CONTAINER_RUNNER=github_actions`, Pantry refuses to start if `PANTRY_CALLBACK_SIGNING_KEY` is unset. This prevents a misconfigured deploy from silently accepting unsigned callbacks.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PANTRY_CALLBACK_SIGNING_KEY` | Yes (GHA runner mode) | Shared HMAC secret. Must match the `PANTRY_CALLBACK_SIGNING_KEY` GHA env secret in the `pantry-callback` environment on `jarvis-pantry-runner`. |
| `PANTRY_CONTAINER_RUNNER` | Yes | Set to `github_actions` in production. |

### Key Rotation

See the [Callback Signing Key Rotation](../ops/callback-signing-key-rotation.md) runbook.

## Database Notes

The `submissions` table uses a `callback_nonce` column (renamed from `callback_token` in jarvis-pantry#25 via `alter_column` — in-flight rows were preserved during the migration).

## Lockfile Size Cap

The resolved dependency lockfile is shipped as a `workflow_dispatch` input. GitHub Actions has a ~64 KB ceiling on dispatch inputs, so Pantry enforces a **50 KB cap** on resolved lockfiles and rejects submissions that exceed it.

Hashless lockfiles (`pip-compile` without `--generate-hashes`) are used since the hash-per-artifact format inflates lockfile size dramatically for packages with many wheel variants. Version pinning is preserved; only the wheel hashes are omitted.

## Apt Package Allowlists

Submissions can declare `apt_packages` to request system package installation on the runner. Pantry validates these against allowlist YAML files that are bundled into the Docker image.

The `config/` directory is copied into both `Dockerfile` and `Dockerfile.fly` via `COPY config/ config/`. It contains:

| File | Purpose |
|------|---------|
| `config/apt-allowlist.yaml` | Packages permitted for installation |
| `config/apt-source-allowlist.yaml` | Apt sources permitted to be added |
| `config/post-install-allowlist.yaml` | Post-install operations permitted |

The allowlist check **fails closed** — if the config directory is absent from the image, any submission that declares `apt_packages` is rejected immediately:

```
Submission failed: apt allow-list config not found: /app/config/apt-allowlist.yaml
```

If you are building or rebuilding the Docker image and see this error, verify that `COPY config/ config/` appears in the Dockerfile before the application entrypoint.

## Forge Package Generation

`POST /v1/forge/generate` generates a Jarvis package from a natural-language description. It's BYOK — the caller supplies their own LLM API key (`llm_api_key` in the request body), used once and never stored.

Because the endpoint is unauthenticated and triggers LLM generation, it carries a per-client-IP rate limit — the tightest cap in the app:

| Variable | Default | Description |
|----------|---------|-------------|
| `FORGE_GENERATE_RATE_LIMIT_PER_HOUR` | `5` | Per-IP cap on `/v1/forge/generate` requests per hour |
| `RATE_LIMIT_DISABLED` | `false` | Set `true` in dev to bypass all rate limits (submission and forge-generation alike) |

Requests over the cap receive `429 Too Many Requests`. The limit check runs before generation starts, so a rate-limited request never reaches the LLM.

## Running Your Own Pantry

Three opt-in features make it practical to run a Pantry on a home or office network. Each is off until its variable is
set, so a deployment that sets none of them behaves exactly as the public Pantry does.

| Feature | Switch | What it does | Needs an admin key? |
|---|---|---|---|
| [Local LLM for the Forge](#local-llm-for-the-forge) | `FORGE_LOCAL_LLM_ENABLED=true` | The Forge generates packages with an OpenAI-compatible server you run (llama-swap, llama.cpp, vLLM, Ollama) | For changes, when `ADMIN_API_KEY` is set |
| [Upstream mirror](#upstream-mirror) | `PANTRY_UPSTREAM_URL=<public Pantry API>` | One catalogue: your packages first, then the public ones | No |
| [Private packages](#private-packages) | `ADMIN_API_KEY` set | Publish a package straight from a Git repository | Yes, always |

`GET /v1/forge/features` reports which are on (`local_llm`, `private_packages`, `upstream_mirror`), and the web interface
hides what is off.

### Local LLM for the Forge

The server address, API key and default model are set on the web interface's Settings page and stored in the
`app_settings` table. `FORGE_LOCAL_BASE_URL`, `FORGE_LOCAL_API_KEY` and `FORGE_LOCAL_MODEL` are first-run defaults only;
a value saved as an empty string was cleared on purpose and does not fall back.

| Method | Path | Admin key | Purpose |
|---|---|---|---|
| `GET` | `/v1/forge/local-llm` | no | `{base_url, has_api_key, default_model, source}`. The key is never returned. |
| `PUT` | `/v1/forge/local-llm` | when set | Save `{base_url, api_key, default_model}`. Omit `api_key` to keep the stored key; `""` clears it. |
| `POST` | `/v1/forge/local-llm/detect` | when set | Test the supplied address and key (or the saved ones) and return `{ok, models, error}` |
| `GET` | `/v1/forge/models` | no | Detected models first as `local:<model>` (the default marked `"default": true`), then hosted models |

While the switch is off, `/v1/forge/local-llm*` return 404 and no local models are listed. Models are found with
`GET {server}/v1/models` and cached for 30 seconds; an unreachable server yields an empty list, not an error. A local
model needs no per-request API key.

| Variable | Default | Description |
|----------|---------|-------------|
| `FORGE_LOCAL_LLM_ENABLED` | `false` | Master switch |
| `FORGE_LOCAL_TIMEOUT` | `900` | Seconds to wait for a local model's reply |
| `FORGE_LOCAL_MAX_TOKENS` | `8192` | Output cap for local models |

The server fetches whatever address is saved. With no `ADMIN_API_KEY` anyone who can reach the port can change it, so
keep an unauthenticated Pantry on a trusted network.

### Upstream Mirror

With `PANTRY_UPSTREAM_URL` set, `GET /v1/commands` and `/v1/categories` merge the public catalogue with your own packages.
Your packages come first and a local name shadows a public one; each item has `"source": "local" | "upstream"`. Detail,
versions and download answer locally first and fall back to the public Pantry. Nodes still clone each package from its
GitHub repository; the Pantry only brokers the lookup.

| Variable | Default | Description |
|----------|---------|-------------|
| `PANTRY_UPSTREAM_URL` | empty (off) | API address of the public Pantry to mirror |
| `PANTRY_UPSTREAM_TTL_SECONDS` | `300` | How long the fetched list is cached |
| `PANTRY_UPSTREAM_TIMEOUT_SECONDS` | `8` | Request timeout |

If the upstream is offline the last good copy is served, or only your own packages if there never was one. Downloading an
upstream-only package while it is offline returns `502`. Nothing is written upstream or stored locally.

### Private Packages

`POST /v1/admin/commands/from-repo` clones a Git repository, validates its manifest and publishes it under a reserved
author `local`; `DELETE /v1/admin/commands/{name}/local` unpublishes it. **This path has no AI review and no container
test**, so it refuses to run unless `ADMIN_API_KEY` is set and requires `X-Admin-Key`.

```bash
curl -X POST "$PANTRY/v1/admin/commands/from-repo" \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H 'Content-Type: application/json' \
  -d '{"github_repo_url": "https://github.com/you/jarvis-cmd-thing", "ref": "v1.0.0"}'
```

A private GitHub repository needs a clone token, in the request (`token`) or `PANTRY_GITHUB_TOKEN`. It is used for the
clone only and is never stored or returned. A node installing a private package needs its own access to the repository.

## Deployment

```bash
fly deploy -a jarvis-pantry-store
```

Alembic migrations run automatically on every container boot via the Fly `CMD`.

```bash
# Check health
curl https://jarvis-pantry-store.fly.dev/health
```
