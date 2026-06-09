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

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_PANTRY_API_URL` | Yes | Base URL of the Pantry Store API |
| `NEXT_PUBLIC_JARVIS_AUTH_URL` | Yes | Auth service URL for token validation |

## Running Locally

```bash
npm install
npm run dev        # dev server on :3000
npm run typecheck  # TypeScript type check
npm run build      # production build
npm start          # serve production build
```

The app is a standard Next.js application and can be deployed to any platform that supports Node.js (Fly.io, Vercel, etc.).
