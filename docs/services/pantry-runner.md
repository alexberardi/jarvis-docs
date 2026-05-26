# Pantry Runner

!!! note "Work in progress"
    Comprehensive Pantry Runner documentation is in [jarvis-docs#11](https://github.com/alexberardi/jarvis-docs/pull/11)
    (covering the two-job workflow, HMAC signing model, Docker sandbox, sdist support, and troubleshooting).
    This page captures a specific operational requirement from
    [jarvis-pantry-runner#4](https://github.com/alexberardi/jarvis-pantry-runner/pull/4) that was not
    included in that draft. **Merge jarvis-docs#11 first, then integrate this section there.**

The Pantry Runner is a GitHub Actions workflow (`container-test.yml`) that runs the Jarvis Command SDK
test harness on community-submitted packages. It runs in two jobs:

- **`test`** — sandboxed harness execution (`--network=none --read-only --memory=128m`), no secrets
- **`callback`** — HMAC-signed result POST back to the Pantry Store, scoped to the `pantry-callback` GHA environment

## Pre-stage Container Requirements

The `test` job runs a **pre-stage step** inside a throwaway `python:3.11-slim` Docker container
(network enabled) to install the Jarvis Command SDK and submission dependencies into a named
Docker volume before the network-isolated harness container runs.

The SDK is installed via a `git+https://` URL:

```
pip install --target=/deps ... git+https://github.com/alexberardi/jarvis-command-sdk.git@<ref>
```

`python:3.11-slim` does **not** include `git`. The pre-stage explicitly installs it:

```sh
apt-get update && apt-get install -y --no-install-recommends git
```

This runs immediately before the pip install inside the pre-stage container. The sandbox container
where submitted code executes is unaffected — it remains `--network=none --read-only` with no git.

### Troubleshooting: "harness produced no output"

If the pre-stage `apt-get install git` step is ever missing or regresses, the pip install fails
silently and the harness container never runs. The runner reports a misleading error:

```
Submission failed: harness produced no output | harness did not write JSON
```

The workflow log will show the real cause in the `Pre-stage sandbox image and deps` step:

```
ERROR: Error [Errno 2] No such file or directory: 'git' while executing command git version
ERROR: Cannot find command 'git' - do you have 'git' installed and in your PATH?
```

This was the root cause of the first post-#26 end-to-end failure (2026-05-20), fixed in
[jarvis-pantry-runner#4](https://github.com/alexberardi/jarvis-pantry-runner/pull/4).
