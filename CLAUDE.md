# jarvis-docs

The Jarvis developer docs site (MkDocs Material), published at https://docs.jarvisautomation.dev. Pages live in `docs/`, the nav and theme in `mkdocs.yml`. The repo root also holds files the site serves outside MkDocs: `.well-known/apple-app-site-association` (the mobile app's Universal Links), `_headers`, `_redirects` and `app-fallback/` (the browser fallback for `/app/*` links). `internal-ops/` is internal runbooks, not published.

## Verify

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest        # runs `mkdocs build --strict` and checks the built site
```

CI (`.github/workflows/ci.yml`) runs the same on every pull request and push to `main`. `./run.sh` serves the site locally on port 7730.

## Deploy

Deploy is **manual**: the user runs `./deploy.sh` (MkDocs build + Cloudflare Pages via wrangler). A merge to `main` deploys nothing. Agents never run `deploy.sh`, `wrangler` or any other deploy.

## Merging (agents)

An agent may squash-merge **its own** PR into `main` once CI has passed, then check main's CI after the merge. **Hold for the user's review** instead, with a note saying why, when the PR:

- touches `.well-known/**`, `_headers`, `_redirects` or `app-fallback/**` (what the live domain serves to the mobile app and browsers);
- touches `deploy.sh` or `mkdocs.yml`;
- touches `docs/security/**` or `internal-ops/**`;
- touches `.github/**`;
- adds or changes any `curl … | sh` (or `| bash`) install line, or a pinned version or checksum in one, anywhere in the docs;
- deletes, renames or weakens a test;
- is marked "needs review" by its author.

Never merge someone else's PR, never force-push to `main`.
