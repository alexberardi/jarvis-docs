# Pantry Runner

The Pantry Runner (`jarvis-pantry-runner`) is a GitHub Actions–based service that executes the Jarvis Command SDK test harness against command submissions received from `jarvis-pantry-store`. Because Fly.io machines cannot run Docker-in-Docker, the runner uses GitHub Actions VMs — which provide a clean, isolated environment per submission at no cost.

## How it works

When `jarvis-pantry-store` accepts a submission, it triggers a `workflow_dispatch` on `jarvis-pantry-runner`. The workflow runs in two jobs:

| Job | Key access | What it does |
|-----|-----------|--------------|
| `test` | None | Clones the submission, runs the SDK harness in the sandbox, uploads results as an artifact |
| `callback` | `PANTRY_CALLBACK_SIGNING_KEY` (env-gated) | Downloads the artifact and POSTs a signed result back to the pantry store |

The signing key never reaches the `test` job — submitted code cannot exfiltrate it.

## Sandbox model

The harness runs inside a Docker container with strict constraints:

| Constraint | Value | Purpose |
|------------|-------|---------|
| Network | `--network=none` | Submitted code cannot reach external services during `run()` |
| Filesystem | `--read-only` | Submitted code cannot write to the container rootfs |
| Memory | `--memory=128m` | Submitted code cannot exhaust runner RAM |
| `/tmp` | `tmpfs` (64 MB) | Allows transient writes without rootfs mutation |

### Two-phase execution

**Pre-stage** (network enabled, runs before the sandbox):

- Pulls `python:3.11-slim`
- Installs the Jarvis Command SDK and the submission's locked dependencies into a named Docker volume (`harness-deps`)
- The `--only-binary=:all:` flag is enforced on the submission lockfile to block sdist build hooks at install time

**Sandbox run** (network disabled):

- Mounts `harness-deps` read-only at `/deps` — submitted code cannot add or modify packages
- Mounts the submission and runner scripts read-only
- Writes harness output only to a dedicated `/output` dir
- Runs `python /runner/harness.py`

This split means the sandbox container has no network access and no writable package store — submitted code cannot install additional packages or reach external services during `run()`.

## Workflow inputs

| Input | Description |
|-------|-------------|
| `submission_id` | Pantry submission UUID |
| `repo` | GitHub repo of the submitted command (`owner/name`) |
| `sha` | Commit SHA to test |
| `sdk_ref` | Branch or tag of `jarvis-command-sdk` to use |
| `lockfile_content` | Pre-resolved `pip-compile` lockfile for the submission's declared dependencies |
| `callback_url` | URL to POST results to |
| `nonce` | Per-submission nonce mixed into the HMAC signature |

## Callback signing

The `callback` job signs the result with HMAC-SHA256 over `{submission_id}|{nonce}|{body_bytes}` using `PANTRY_CALLBACK_SIGNING_KEY`. The pantry store verifies the signature before accepting results. The signing key is scoped to the `pantry-callback` GHA environment and is never exposed to the `test` job or to submitted code.
