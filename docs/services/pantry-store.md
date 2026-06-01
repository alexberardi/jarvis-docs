# Pantry Store

Pantry Store (`jarvis-pantry`) is the backend service for the Jarvis Pantry command marketplace. It manages command submissions, lockfile resolution, container test dispatch via GitHub Actions, and HMAC-signed callback verification.

!!! note "Comprehensive reference in draft"
    A full Pantry Store reference covering the submission pipeline, HMAC callback security model, lockfile size cap, apt allowlists, and env vars is in draft — see [jarvis-docs#12](https://github.com/alexberardi/jarvis-docs/pull/12). This page captures the deployment-critical alembic migration chain fix from [jarvis-pantry#12](https://github.com/alexberardi/jarvis-pantry/pull/12).

## Database Migrations

Pantry Store uses Alembic for schema management. The Fly deployment (`jarvis-pantry-store`) runs `alembic upgrade head` on every container boot as part of the `Dockerfile.fly` CMD.

### Migration chain (current head as of 2026-05-20)

After pantry#11 (HMAC callbacks) and pantry#12 (chain fix), the linearized history is:

```
... → e2f3a4b5c6d7
    → f3a4b5c6d7e8  (resolved_lockfile)
    → a4b5c6d7e8f9  (callback_timeout columns, #22)
    → g4b5c6d7e8f9  (rename callback_token → callback_nonce)  ← HEAD
```

Verify with:

```bash
alembic heads          # must report exactly one head
alembic history | head -5
```

### Troubleshooting: container crashes with "Multiple head revisions"

**Symptom** — Fly deployment loops and never becomes healthy. Container log shows:

```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow to a specific head,
or 'heads' for all heads
```

Container exits 255 on every boot.

**Root cause** — This crash loop affected the `jarvis-pantry-store` Fly deployment between
pantry#11 merged (2026-05-20T01:41Z) and pantry#12 merged (2026-05-20T01:49Z). The
`g4b5c6d7e8f9` migration (renaming `callback_token → callback_nonce`) mistakenly claimed
`f3a4b5c6d7e8` as its parent, but `a4b5c6d7e8f9` (callback-timeout columns from #22) was
already chained off that same parent — producing two Alembic heads. `alembic upgrade head`
refuses to run against a graph with multiple heads.

**Fix** — pantry#12 re-pointed `g4b5c6d7e8f9.down_revision` from `f3a4b5c6d7e8` to
`a4b5c6d7e8f9`. If you encounter this error on a deployment predating pantry#12, redeploy
from the current `main`:

```bash
fly deploy -a jarvis-pantry-store
```
