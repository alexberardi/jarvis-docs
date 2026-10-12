# Pantry Web

**Repo**: [`alexberardi/jarvis-pantry-web`](https://github.com/alexberardi/jarvis-pantry-web)  
**Stack**: Next.js (App Router), TypeScript, Tailwind CSS, CodeMirror

The Pantry Web is the browser-based interface for the Jarvis Pantry — a marketplace for community-built voice commands. Developers use it to browse published packages, submit new commands, and iterate with the live static-analysis preview tool (Forge).

## Pages

| Route | Purpose |
|---|---|
| `/commands` | Catalog of published Pantry commands |
| `/commands/<slug>` | Command detail — description, install status, test results |
| `/submit` | Package submission form with static-analysis preview |
| `/forge` | Full CodeMirror editor with live static-analysis preview |
| `/settings` | Local LLM server address, key and default model, with model detection. Shown only when the backend reports `local_llm`. |
| `/private` | Add, list and unpublish private packages from a Git repository. Shown only when the backend reports `private_packages`. |

## Authentication

Authentication is `localStorage`-backed and SSR-safe via `useSyncExternalStore`. The server snapshot is always unauthenticated (`null`), so SSR and the first client render agree. The stored session is read after hydration.

Two events trigger re-renders across components and tabs:

- **`pantry-auth-change`** — fired internally on login, logout, and token validation
- **`storage`** — native browser event for cross-tab sync

The `Header` component reflects auth state: anonymous users see **Sign in**; authenticated users see a user dropdown.

## Static-Analysis Preview (Forge and `/submit`)

Before a package is dispatched to the container runner, the backend returns a `StaticAnalysisResult`. Its fields are optional because older server builds may omit them:

| Field | Type | Notes |
|---|---|---|
| `findings` | `Finding[]` (optional) | Policy violations |
| `warnings_structured` | `Finding[]` (optional) | Structured warnings; replaces the legacy `warnings: string[]` field |

The UI reads both with a `?? []` fallback so a missing field never causes a runtime crash. Each finding renders as a `FindingCard`.

## Self-Hosting Pages

`/settings` and `/private` exist for a Pantry run on your own network (see
[Running Your Own Pantry](../pantry/self-hosting.md)). On load the header calls `GET /v1/forge/features`, which returns
`{local_llm, private_packages, upstream_mirror}`, and shows the **Settings** and **Private** links accordingly. A backend
without the route simply reads as "everything off", so nothing extra appears and nothing breaks. Each page also checks
the flag itself, so opening its URL directly on a Pantry without the feature says it is unavailable.

- **Settings** shows what the backend has saved (never the key itself; the server address only once the admin key has
  been entered, since the backend does not reveal it to anyone else). **Detect models** asks the *backend* to list the
  model server's models, and **Save** stores the address, key and default. The browser never contacts the model server.
- **Forge** lists detected local models first (`local:<model>`, free) and preselects the default. The API-key field is
  disabled for them and the page sends an empty key, because the backend uses its saved server and key and ignores one
  supplied by the caller.
- **Private** posts a repository URL (optional tag or branch, optional GitHub token) to
  `POST /v1/admin/commands/from-repo` and lists the packages whose `source` is `local`: only the ones an administrator
  added from a repository. Packages published through the Pantry's pipeline (`pantry`) and mirrored ones (`upstream`)
  are not listed, so **Unpublish** is only offered for packages it can act on.

**Admin key.** Changing the settings and adding or unpublishing a private package need the Pantry's `ADMIN_API_KEY`,
sent as `X-Admin-Key`. The pages keep it in `sessionStorage`, so it lasts for that browser tab only and is never written
to disk or a cookie. A `401` is reported as an admin-key problem, not a model-server one.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_PANTRY_API_URL` | Yes | Base URL of the Pantry Store API |
| `NEXT_PUBLIC_JARVIS_AUTH_URL` | Yes | Auth service URL for token validation |
| `PANTRY_API_URL` | No (default `http://localhost:7721`) | Backend address the server-side `/v1/*` and `/health` rewrites proxy to |

!!! warning "Both addresses are baked into the build"
    `next.config.ts` fixes the rewrite target when `next build` runs, and `NEXT_PUBLIC_*` values are inlined into the
    browser bundle. Changing either needs a rebuild, not a restart. `NEXT_PUBLIC_PANTRY_API_URL` must be an address the
    *browser* can reach (a LAN address on a server, not `localhost`).

## Running Locally

```bash
npm install
npm run dev        # dev server on :3000
npm run typecheck  # TypeScript type check
npm run build      # production build
npm start          # serve production build
```

The app is a standard Next.js application and can be deployed to any platform that supports Node.js (Fly.io, Vercel, etc.).
