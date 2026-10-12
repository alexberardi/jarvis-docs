# Running Your Own Pantry

The public Pantry is the default store every node reads from. You can also run a Pantry of your own on a home or office
network. Three opt-in features make that useful:

| Feature | Switch | What it gives you |
|---|---|---|
| [Local LLM for the Forge](#local-llm-for-the-forge) | `FORGE_LOCAL_LLM_ENABLED=true` | The Forge generates packages with a model on your own hardware: free, and nothing leaves your network |
| [Upstream mirror](#upstream-mirror) | `PANTRY_UPSTREAM_URL=<public Pantry API>` | One catalogue that lists the public packages and yours together |
| [Private packages](#private-packages) | `ADMIN_API_KEY` set | Publish an integration from a Git repository without making it public |

Each is **off until its variable is set**. A Pantry that sets none of them behaves exactly like the public one. The
implementation lives in [`jarvis-pantry`](https://github.com/alexberardi/jarvis-pantry) (see
[Pantry Store](../services/pantry-store.md)) and the interface in
[`jarvis-pantry-web`](https://github.com/alexberardi/jarvis-pantry-web) (see [Pantry Web](../services/pantry-web.md)).

## How it fits together

```
 Jarvis node ──(command_store_url)──┐
                                    ▼
 browser ──▶ jarvis-pantry-web ──▶ jarvis-pantry (:7721) ──▶ PostgreSQL
              (:7720)                │   │  │
                                     │   │  └──▶ public Pantry   (PANTRY_UPSTREAM_URL, read-only, cached)
                                     │   └─────▶ GitHub          (clone a repository to publish it)
                                     └─────────▶ your LLM server (/v1/models, /v1/chat/completions)
```

A node still installs a package by cloning its GitHub repository. The Pantry only brokers the lookup (name, versions,
repository URL and pinned commit); it never hosts package contents.

## Quick start

`jarvis-pantry` ships a compose file that runs the database, the API and the web interface on one machine:

```bash
git clone https://github.com/alexberardi/jarvis-pantry
git clone https://github.com/alexberardi/jarvis-pantry-web      # sibling directory; built by the compose file
cd jarvis-pantry
cp .env.local.example .env.local         # set PANTRY_DB_PASSWORD (and PANTRY_PUBLIC_API_URL on a server)
docker compose -f docker-compose.local.yaml --env-file .env.local up -d --build
```

| Service | Port | Notes |
|---|---|---|
| `pantry` | 7721 | The API. Swagger UI at `/docs`. Migrations run on start. |
| `pantry-web` | 7720 | The web interface |
| `pantry-db` | internal | PostgreSQL 16 |

Variables in `.env.local`:

| Variable | Default | Purpose |
|---|---|---|
| `PANTRY_DB_PASSWORD` | required | Database password |
| `PANTRY_PUBLIC_API_URL` | `http://localhost:7721` | Address the **browser** uses to reach the API. Baked into the web build, so rebuild after changing it. On a server use its LAN address. |
| `FORGE_LOCAL_LLM_ENABLED` | `true` | Master switch for the local LLM features |
| `PANTRY_UPSTREAM_URL` | public Pantry API | Catalogue to mirror; blank for your own packages only |
| `PANTRY_GITHUB_TOKEN` | blank | Clone token for private GitHub repositories |
| `PANTRY_ADMIN_API_KEY` | blank | Becomes `ADMIN_API_KEY` in the container |
| `FORGE_LOCAL_BASE_URL` / `_API_KEY` / `_MODEL` | blank | First-run defaults; normally set from Settings |

The compose file mounts no Docker socket, so the sandboxed container tests that run when a package is **submitted
through the public flow** are unavailable. Generating and downloading work.

## Local LLM for the Forge

The Forge can build packages with any OpenAI-compatible server you run: llama-swap, llama.cpp `llama-server`, vLLM or
Ollama.

1. Set `FORGE_LOCAL_LLM_ENABLED=true`. While it is off, the Settings page is hidden, the `/v1/forge/local-llm*`
   endpoints return 404 and no local model is listed.
2. Open the web interface, go to **Settings**, enter the server's address (and its API key if it has one) and press
   **Detect models**. The Pantry asks the server for `GET /v1/models`.
3. Choose a default model and **Save**.

The detected models appear first in the Forge's model list as `local:<model>`, marked free. Choosing one needs no API
key: the request goes to your Pantry, which calls `{server}/v1/chat/completions` with the saved key. Replies get a long
read timeout (`FORGE_LOCAL_TIMEOUT`, default 900 seconds, because local models are slow) and any `<think>` block is
removed before the reply reaches the Forge.

**Where the settings are stored.** The server address, key and default model live in the Pantry's database
(`app_settings` table), so they survive restarts and apply to everyone using that Pantry. `FORGE_LOCAL_BASE_URL`,
`FORGE_LOCAL_API_KEY` and `FORGE_LOCAL_MODEL` are first-run fallbacks only; a saved value wins. The key is never returned
by any endpoint, only whether one is set.

**Limits.** Local models are slower and weaker than hosted ones, and the Forge's static checks do not import or run the
generated code, so test what it produces.

## Upstream mirror

Set `PANTRY_UPSTREAM_URL` to the public Pantry's API and your Pantry lists the public catalogue **and** its own packages
as one store, so a node needs only one address.

- `GET /v1/commands` merges both: your packages first, then the public ones. A local name **shadows** a public one. Each
  item carries `"source": "local"` or `"upstream"`, and search, category and type filters, sorting and pagination apply to
  the merged list. `/v1/categories` counts both.
- `GET /v1/commands/{name}`, `/versions` and `/download` answer locally first and fall back to the public Pantry.
- The public list is cached for `PANTRY_UPSTREAM_TTL_SECONDS` (default 300) with a request timeout of
  `PANTRY_UPSTREAM_TIMEOUT_SECONDS` (default 8). If the public Pantry is unreachable, the last good copy is served, or
  only your own packages when there never was one. A download of an upstream-only package has no copy to fall back on
  and answers `502`.
- The mirror is read-only: nothing is written upstream.

Point a node at your Pantry by setting `command_store_url` in its configuration to the Pantry's address, for example
`http://pantry.lan:7721`. Its default is the public Pantry's API.

## Private packages

The public submission flow needs GitHub login, an AI security review and container tests. For repositories you own there
is an administrator shortcut:

```bash
curl -s -X POST http://pantry.lan:7721/v1/admin/commands/from-repo \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H 'Content-Type: application/json' \
  -d '{"github_repo_url": "https://github.com/you/jarvis-cmd-thing", "ref": "v1.0.0"}'
```

The Pantry clones the repository at `ref` (a tag or branch; the default branch when omitted), validates the manifest with
the same structure check the public flow uses, and publishes it as a local package under a reserved `local` author. The
response reports the package name, version, whether it is a `command` or a `bundle`, and the commit it pinned. Run the
request again with a new `ref` to publish a new version.

!!! warning "No security review"
    A package added this way gets **no AI review and no container test**, because nodes install whatever you add. The
    endpoint therefore refuses to run (`403`) unless `ADMIN_API_KEY` is set. Only add repositories you trust.

- **Private GitHub repositories.** Supply a token in the request (`token`) or set `PANTRY_GITHUB_TOKEN`. It is used for
  the clone only, is never stored and is removed from error text. A node installing a private repository needs its own
  access to it.
- **It never replaces a reviewed package.** If a package with that name already exists and was not added through this
  endpoint (a public submission, for example), the request is refused with `409`. Rename the package in the manifest or
  unpublish the existing one first.
- **"Private" means unreviewed and local, not secret.** A package added this way is listed, shown and downloadable
  through the same public routes as every other package on this Pantry (`"source": "local"`, against `"pantry"` for a
  public submission and `"upstream"` for a mirrored package). Keep the Pantry on a
  network where that is acceptable, or put an access-controlled proxy in front of it.
- **Unpublish.** `DELETE /v1/admin/commands/{name}/local` hides a package; it is not deleted, and publishing the same
  name again brings it back. Only packages added this way can be unpublished here.
- **In the web interface** the **Private** page does the same add, list and unpublish from a form. It appears only when
  the Pantry has an admin key, and it lists only the packages added this way (`source` is `local`), never public
  submissions or mirrored packages.

## The admin key

`ADMIN_API_KEY` is one shared secret, sent as the `X-Admin-Key` header. It is not a login or a JWT.

| Action | With no key set | With a key set |
|---|---|---|
| Change or probe the local LLM server (`PUT` and `detect`) | **refused** (`403`) | needs the key |
| Add or unpublish a private package | **refused** (`403`) | needs the key |
| Existing moderation endpoints | unchanged | unchanged |

A wrong or missing key is `401`. The key is compared in constant time. Endpoints that change what nodes install or where
the Pantry sends requests never run on an open Pantry. The saved model-server API key is only ever sent to the saved
server; probing another address with `detect` uses the key in that request, never the saved one. The web interface keeps
the admin key in the browser tab's `sessionStorage` only.

## Checking what is enabled

```bash
curl -s http://pantry.lan:7721/v1/forge/features
# {"local_llm": true, "private_packages": true, "upstream_mirror": true, "admin_key_configured": true}
```

The web interface reads this to decide which links to show.

## Troubleshooting

| Symptom | Cause |
|---|---|
| "The admin key is missing or wrong" on **Detect models** or **Save** | The Pantry's own `ADMIN_API_KEY` (not the model server's key) is missing from the **Admin key** field |
| **Detect models** reports it could not reach the server | The Pantry, not your browser, calls the model server. The address must be reachable from the Pantry's container. |
| Settings link missing | `FORGE_LOCAL_LLM_ENABLED` is not `true` on the Pantry |
| **Private** page says it is unavailable | The Pantry has no `ADMIN_API_KEY` |
| Forge works but the browser shows network errors | `PANTRY_PUBLIC_API_URL` is `localhost` but you are browsing from another machine; set it to a reachable address and rebuild |
| Nothing public shows up in the catalogue | `PANTRY_UPSTREAM_URL` is blank |
