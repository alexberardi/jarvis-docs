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
|----------|----------|--------------|
| `PANTRY_CALLBACK_SIGNING_KEY` | Yes (GHA runner mode) | Shared HMAC secret. Must match the `PANTRY_CALLBACK_SIGNING_KEY` GHA env secret in the `pantry-callback` environment on `jarvis-pantry-runner`. |
| `PANTRY_CONTAINER_RUNNER` | Yes | Set to `github_actions` in production. |

### Key Rotation

See the [Callback Signing Key Rotation](../ops/callback-signing-key-rotation.md) runbook.

## Database Notes

The `submissions` table uses a `callback_nonce` column (renamed from `callback_token` in v18 via `alter_column` — in-flight rows were preserved during the migration).

## Lockfile Size Cap

The resolved dependency lockfile is shipped as a `workflow_dispatch` input. GitHub Actions has a ~64 KB ceiling on dispatch inputs, so Pantry enforces a **50 KB cap** on resolved lockfiles and rejects submissions that exceed it.

Hashless lockfiles (`pip-compile` without `--generate-hashes`) are used since the hash-per-artifact format inflates lockfile size dramatically for packages with many wheel variants. Version pinning is preserved; only the wheel hashes are omitted.

## Deployment

```bash
fly deploy -a jarvis-pantry-store
```

Alembic migrations run automatically on every container boot via the Fly `CMD`.

```bash
# Check health
curl https://jarvis-pantry-store.fly.dev/health
```
