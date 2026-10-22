# jarvis-docs

The Jarvis developer docs site (MkDocs Material), published at https://docs.jarvisautomation.dev. Pages live in `docs/`, the nav and theme in `mkdocs.yml`. The repo root also holds files the site serves outside MkDocs: `.well-known/apple-app-site-association` (the mobile app's Universal Links), `_headers`, `_redirects` and `app-fallback/` (the browser fallback for `/app/*` links). `internal-ops/` is internal runbooks, not published.

## Verify

```bash
.venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest        # runs `mkdocs build --strict` and checks the built site
```

On the dev box, every Python shim on the PATH — `python`, `python3`, `python3.11`, `pip`, `mkdocs` — is a mise shim with no Python version set, so any of them fails at once (`mise ERROR No version is set for shim`). Verify and proof commands must not rely on PATH and must never create the venv: the loop runner creates `.venv`, so a proof or verify command starts with `.venv/bin/python -m pip install …`. The proof command for a docs PR:

```bash
.venv/bin/python -m pip install -q -r requirements.txt -r requirements-dev.txt && .venv/bin/mkdocs build --strict && .venv/bin/python -m pytest -q
```

Outside the loop (a laptop or CI), create the venv first with `python3.11 -m venv .venv` if your box has a real `python3.11` (no version needed: use any installed Python 3.11, e.g. `~/.local/share/mise/installs/python/3.11.16/bin/python3.11`). Do not add a `mise.toml` to fix this: mise does not trust a config in a fresh checkout, so every shim call would fail.

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

## Page and theme work loads the design skills

Any change to how the site looks or reads (theme CSS, `mkdocs.yml` theme settings, page layout, a new page or section, diagrams, copy structure) loads the three skills in `.claude/skills/` before the first edit: **impeccable** (system rules, commands, the audit checklist), **emil-design-eng** (every motion decision) and **design-taste-frontend** (layout, type and spacing feel). Where they disagree, `.claude/skills/DESIGN-SKILLS.md` decides: accessibility and contrast first, then Impeccable's system rules, Emil for motion, Taste for layout feel.

They are copied unchanged from jarvis-server (`.claude/skills/`, at 1fd33737); change them there through DESIGN-SKILLS.md's process, then copy them here again. They were written for jarvis-server's `web/admin`; in this repo read them as:

- **Design system:** direction B ("Quiet Violet", chosen in jarvis-server #331; source values in jarvis-server `docs/design/directions/tokens.py`), mapped onto MkDocs Material in `docs/assets/stylesheets/theme.css` and pinned by `tests/test_theme.py`. Where a skill says `web/admin/src/index.css`, `.dark` or `src/theme/`, read `theme.css` and its `[data-md-color-scheme]` blocks. Extend B; don't introduce new colours, fonts or a second style. System font stacks only; nothing is fetched.
- **Mode:** Read (`impeccable/reference/mode-read.md`) for doc pages: content first, scannable headings, short paragraphs, tables for comparisons, admonitions sparingly. The home page's cards may use Persuade lightly.
- **Taste's dials here:** variance 3, motion 2, density 4 (reading, slightly airier than the app's 5).
- **No libraries:** no MkDocs plugins, JS, icon or font packages added for design work; Material's built-ins and inline SVG only.
- **Rendered check:** there is no `scripts/sandbox` or `scripts/screenshots` here. Build the site (`.venv/bin/mkdocs build --strict`, or `./run.sh` on port 7730) and look at the changed pages at phone (390 px), tablet and desktop widths in both colour schemes with the headless browser the runner has; if none is available, say so and list the visual checks under "not verified".

Before a PR that changes the theme or page structure: run Impeccable's audit (`.claude/skills/impeccable/reference/audit.md`) over the changed pages, fix what it finds, and put its findings report (and the screenshots, if any) in the PR body.
