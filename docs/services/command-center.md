# Command Center

The command center is the voice command orchestrator. It receives transcribed text (or raw audio) from nodes, routes it through the LLM for intent parsing and tool selection, executes the appropriate command, and returns the response. It also manages node registration, user memories, and speaker identification.

## Quick Reference

| | |
|---|---|
| **Port** | 7703 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-command-center/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL (pgvector required — see Dependencies) |
| **Tier** | 2 - Command Processing |

## API Endpoints

| Method | Path | Description |
|--------|------|--------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v0/voice/command` | Process a voice command (requires a warmed `conversation_id` from `POST /api/v0/conversation/start`) |
| `POST` | `/api/v0/nodes/register` | Register a new node (admin) |
| `GET` | `/api/v0/admin/nodes` | List registered nodes (admin token) |
| `GET` | `/api/v0/memories` | List user memories |
| `POST` | `/api/v0/memories` | Create a user memory |
| `DELETE` | `/api/v0/memories/{id}` | Delete a user memory |
| `GET` | `/api/v0/node/mqtt-credentials` | Shared MQTT broker credentials for the authenticated node (see [MQTT Broker Auth](#mqtt-broker-auth-transition)) |
| `POST` | `/api/v0/nodes/tasks/{task_id}/status` | Node self-reports a terminal status for its own task (see [Node Task Status Reporting](#node-task-status-reporting)) |

For mobile data-browser routes see [Mobile Command-Data API](#mobile-command-data-api) below.

For household settings routes (e.g. web search toggle) see [Mobile Household Settings API](#mobile-household-settings-api) below.

For camera streaming routes see [Camera Streaming](#camera-streaming) below.

For phone-call routes see [Phone Calls](#phone-calls) below.

## Blocking Voice Command Error Contract

Added in jarvis-command-center#18. The blocking voice endpoints — `POST /api/v0/voice/command` and `POST /api/v0/voice/command/continue` — now return **422 Unprocessable Entity** for whole-request precondition failures (e.g. an unknown or expired `conversation_id`) instead of swallowing them into a `200` response with an `errors` payload.

**Before:** a broad `except Exception` around both endpoints caught every exception, including precondition failures, and re-wrapped them as `200` `VoiceCommandResponse` bodies with an `errors` field — callers had to inspect the response body to detect a rejected request.

**After:** a dedicated `ConversationPreconditionError` is raised for "conversation not found or expired" checks and mapped to `422` ahead of the broad exception handler. The inline "Conversation not initialized for tool-based flow" precondition also moved from `400` to `422` for consistency.

**Unaffected:**

- Legitimate per-command / partial-batch failures still return `200` with `commands[].success=false`.
- Genuine internal errors are not remapped to `422`.
- The non-blocking streaming endpoints (`/voice/command/stream`, `/voice/command/continue/stream`) keep their existing `200`-shaped partial-batch semantics — untouched by this change.

## Mobile Command-Data API

The mobile app manages command records through a set of REST routes that proxy to the node's MQTT data-browser protocol. All routes require a valid mobile JWT.

| Method | Path | Description |
|--------|------|--------------|
| `GET` | `/command-data/nodes` | List nodes visible to the authenticated user |
| `GET` | `/command-data/nodes/{node_id}/commands/{command_name}/schema` | Fetch field schema for a command |
| `GET` | `/command-data/nodes/{node_id}/commands/{command_name}/records` | List all records |
| `GET` | `/command-data/nodes/{node_id}/commands/{command_name}/records/{key}` | Fetch one record |
| `POST` | `/command-data/nodes/{node_id}/commands/{command_name}/records` | **Create** a new record |
| `PATCH` | `/command-data/nodes/{node_id}/commands/{command_name}/records/{key}` | Update (patch) a record |
| `DELETE` | `/command-data/nodes/{node_id}/commands/{command_name}/records/{key}` | Delete a record |

### Creating a Record (`POST .../records`)

Added in jarvis-command-center#19. The client sends only field values; the node mints the storage key and stamps the owner from the JWT-resolved caller — ownership is never client-asserted.

**Request body:**

```json
{ "data": { "name": "Vitamin D", "scope": "personal" } }
```

**Response (200):**

```json
{ "record": { "id": "...", "user_id": 42, ... }, "key": "..." }
```

**Error mapping:**

| Node error | HTTP status |
|---|---|
| Command is read-only | 403 |
| Command not found / does not support create | 404 |
| Validation failure (e.g. "at least one dose time is required") | 400 |

The mobile app shows 400 error messages directly to the user so commands should phrase `ValueError` messages in plain language.

### Schema Response — `supports_create`

The schema endpoint (and the inline schema in the get-record response) now includes `supports_create`:

```json
{
  "mode": "enabled",
  "supports_create": true,
  "fields": [
    { "name": "name", "type": "string", "editable": true },
    { "name": "scope", "type": "enum", "editable": false, "create_only": true,
      "enum_values": ["personal", "household"] }
  ]
}
```

The mobile app gates its **+** button on `supports_create`. Commands that do not override `data_browser_supports_create` return `false` and the button is hidden.

See [Data Browser Protocol](../extending/infrastructure/datastore.md#data-browser-protocol) for the command-authoring side (how to opt a command into create support).

## Mobile Household Settings API

Added in jarvis-command-center#20. A dedicated router (`app/api/mobile_household_settings.py`) exposes an allowlisted set of household-level settings that a household admin can toggle from the mobile app. The shared `/settings/*` router requires global `is_superuser` — the wrong scope for a per-household toggle — so this router authorizes writes via the caller's role in the target household instead.

**Auth:** reads require `member` role; writes require `admin` role in the target household.

**Allowlisted settings:**

| Key | Type | Description |
|---|---|---|
| `web_search.enabled` | `bool` | Master toggle for outbound-web tools (`quick_search` + `deep_research`). Default `false`. |
| `web_scraping.allow_external` | `bool` | Allow deep research to fall back to the r.jina.ai reader proxy when a page cannot be fetched directly. Enables egress to a third party — opt-in per household. Default `false`. |

Any key not on the allowlist returns `404` — the allowlist is the security boundary that prevents this endpoint from becoming a household-admin write path to arbitrary command-center settings.

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v0/mobile/household/{household_id}/settings` | Any household member | Returns current values of all household-controllable settings |
| `PUT` | `/api/v0/mobile/household/{household_id}/settings/{key}` | Household admin | Sets one household-controllable setting |

**PUT request body:**

```json
{ "value": true }
```

**PUT response (200):**

```json
{ "success": true, "key": "web_search.enabled", "value": true }
```

Values fall back to the code default when no override row exists in the DB — no seed data is required for new households.

## Smart Home Devices

### Protocol Cleanup on Delete

Added in jarvis-command-center#21. When a `direct`-protocol device (a device managed by a node-side device protocol package) is deleted from a household, command-center publishes a `device_removed` MQTT message to the node that owns that device's protocol **before** the database record is dropped.

This lets the node call the protocol's `on_removed` hook to release any external pairing or session — for example, a HomeKit accessory is unpaired at the HAP layer so it can be re-added and re-paired cleanly.

**Behaviour:**

- **Best-effort:** if MQTT or the node is unavailable, the delete still proceeds (the node retains an orphaned pairing until its next restart or rediscovery).
- **Scope:** only `source="direct"` devices with a `protocol` field. Cloud-imported or protocol-less devices are unaffected.
- **No user action required:** the cleanup fires automatically on every device delete.

| Field | Detail |
|---|---|
| Trigger | `DELETE /api/v0/households/{id}/devices/{device_id}` |
| MQTT message type | `device_removed` |
| Payload fields | `entity_id`, `protocol`, `domain`, `cloud_id`, `local_ip`, `mac_address`, `name` |
| Failure policy | Warning logged; delete proceeds regardless |

See [`on_removed` — Device Deletion Hook](../extending/devices/protocols.md#on_removed-device-deletion-hook-sdk-v042) for the protocol authoring side.

### Camera Streaming

Reworked in jarvis-command-center#38 (the last of a 4-repo change: jarvis-command-sdk → jarvis-device-nest → jarvis-node-setup → jarvis-command-center). Command-center no longer builds the go2rtc source URL itself — it asks the owning node for one and registers whatever comes back **verbatim**, with no protocol-specific knowledge of its own.

**Flow:**

1. Mobile calls `POST /api/v0/households/{household_id}/cameras/{device_id}/stream` with an **empty body** — no credentials are ever sent by the client.
2. CC publishes `{request_id, protocol, cloud_id, entity_id, domain}` to `jarvis/nodes/{node_id}/camera-credentials` over MQTT (full, unstripped `cloud_id`).
3. The node resolves the device-protocol plugin for `protocol` and awaits its `get_stream_source(device)` hook — see [`get_stream_source` — Camera Streaming Hook](../extending/devices/protocols.md#get_stream_source-camera-streaming-hook-sdk-v050).
4. The node POSTs `{"stream_source": "..."}` (or `{"error": "..."}`) back to `POST /api/v0/camera-credentials/{request_id}` (node `X-API-Key` auth).
5. CC registers `stream_source` with go2rtc verbatim and returns a proxied HLS URL.

**Breaking change:** `StartStreamRequest` dropped its legacy body fields (`refresh_token`, `client_id`, `client_secret`, `project_id`, `protocols`) along with the `nest:` URL builder and the hardcoded `protocols=RTSP` default. That default forced `400`s (then retry `429`s) from WebRTC-only cameras like the battery Nest Doorbell — the node-side protocol plugin now picks the transport instead (see the Nest reference implementation in the protocols doc). Callers must send an empty body; credentials are never client-supplied.

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v0/households/{household_id}/cameras` | Household member | List camera devices for a household |
| `POST` | `/api/v0/households/{household_id}/cameras/{device_id}/stream` | Household member | Start a stream; registers the node's go2rtc source |
| `DELETE` | `/api/v0/households/{household_id}/cameras/{device_id}/stream` | Household member | Stop a stream and remove it from go2rtc |
| `POST` | `/api/v0/camera-credentials/{request_id}` | Node `X-API-Key` | Node callback with the built stream source (or an error) |
| `GET` | `/api/v0/cameras/stream/{stream_name}/{path}` | Household member (stream owner) | Proxy HLS/MP4 segments from go2rtc |

The HLS proxy restricts `{path}` to media file suffixes (`.m3u8`, `.ts`, `.mp4`, `.m4s`, `.aac`, `.vtt`, `.key`) so it cannot be pivoted to go2rtc control endpoints like `/api/config`, which would disclose every household's camera/OAuth credentials.

## Phone Calls

Added in jarvis-command-center#57 (`jarvis/prds/phone-calls.md` P1), on top of #55 (server-plane callback dispatch) and #56 (household-settings int coercion). This is the CC half of the phone-calls feature — see [Phone Gateway](phone-gateway.md) for the Twilio-facing worker that actually dials.

### `make_phone_call` Server Tool

A `deep_research`-shaped server tool: spoken acknowledgment → background number resolve + plan draft → an editable confirm card. It is **always offered in the text-path tool whitelist**, even when the feature is disabled — a disabled `execute()` returns an honest spoken refusal instead of leaving the model to improvise a fake capability (the fix for a live finding where the model hallucinated device-control behavior for "Call Tony's Pizzeria"). The tool fails closed if the caller could not be identified as a speaker.

### Data Model

Migration `c3d4phone001` adds:

- **`phone_call_sessions`** — state machine `draft → confirmed → dialing → in_call → wrapup → done|failed|declined|expired`, with a full audit trail: resolved vs. dialed number, `number_edited`, `confirmed_by`.
- **`phone_contacts`** — the household phonebook, with DNC (do-not-call) enforcement checked at resolve time.

### The Confirm Tap Is the Authorization

Per the PRD's security requirements, tapping "confirm" on the plan card is the sole authorization point for actually dialing:

- Single-use, atomic `draft → confirmed` transition via the `confirm_call` server callback.
- The (possibly user-edited) number is re-validated at confirm time: E.164, US-only, emergency/short-code/premium numbers denied.
- Caps are re-checked at confirm time (not just plan time).
- On success, the job is enqueued via `LPUSH phone:dial` (Redis) for the phone gateway's dial worker to pick up.
- **Enqueue failure lands the session `failed` with an honest card — never a stuck `confirmed`.**

Other server callbacks: `cancel_call`, and `escalation_answer` (forwards the household's typed answer to the gateway worker that claimed the call — see [Escalation Event](#escalation-event) below).

### Gateway-Facing Endpoints

Endpoints matching `jarvis-phone-gateway/services/session_client.py`'s contract shape-for-shape:

| Purpose | Description |
|---|---|
| Session snapshot | The gateway `GET`s the current session state before dialing |
| `claim_dial` (CAS) | Atomic `confirmed → dialing` compare-and-set — single winner; a losing race returns `409` and the gateway drops the job (the queue is transport, never authorization) |
| State transitions | All state changes for a session funnel through one choke point |
| Turn append | Doubles as a heartbeat — CC uses turn recency as a liveness signal for the reaper |
| Outcome | Delivers the attributed call summary card. Callee statements are always labeled as the business's, never rendered as Jarvis's own voice |

#### Escalation Event

The gateway posts `{type: "escalation", question}` when the on-call agent hits `[ESCALATE:]` mid-call (see [Phone Gateway: Call Lifecycle](phone-gateway.md#call-lifecycle)). Valid only while the session is `in_call`; an empty `question` is rejected with `400`. On a valid event, CC pushes an answer card to the initiating user — the question is attributed (never tappable, never rendered as Jarvis speaking), with a multiline answer editor that feeds `escalation_answer`, plus an end-call chip. The card carries a 10-minute TTL; the *real* ~25 s answer window is enforced gateway-side, so a late tap degrades through the existing "call may have ended" path.

### Line-Type Lookup

Number line-type lookup (mobile vs. landline, for UX hints) is delegated to the gateway's `POST /internal/lookup/line-type` — the gateway holds the Twilio credentials, CC never does. Degrades to `unknown` on lookup failure or gateway unavailability.

### Caps and the Reaper

Daily, concurrent, and monthly-minutes caps are enforced fail-closed at both plan time and confirm time. A 30 s reaper sweep fails sessions with a stale heartbeat or an over-limit duration (honest notification to the user + best-effort cancel request to the gateway worker), and expires stale, never-confirmed drafts.

### `phone_calls.*` Settings

Eight `phone_calls.*` settings control the feature, all household-admin editable via the [Mobile Household Settings API](#mobile-household-settings-api) allowlist. **`phone_calls.enabled` defaults to `false`** (fail-closed) — the tool speaks an honest refusal instead of dialing while disabled. Numeric settings (e.g. `plan_ttl_minutes`, `audio_retention_days`, the daily/concurrent/monthly caps) required the int-coercion support added in jarvis-command-center#56 (the allowlist coercion helper was previously bool-only).

## Key Components

- **Prompt Engine** (`app/core/prompt_engine.py`) -- builds system prompts with speaker context and memories
- **Tool Parser** (`app/core/tool_parser.py`) -- extracts tool calls from LLM responses
- **Tool Executor** (`app/core/tool_executor.py`) -- dispatches tool calls to the appropriate service
- **Speaker Resolver** (`app/core/utils/speaker_resolver.py`) -- maps speaker IDs to display names
- **Memory Service** (`app/services/memory_service.py`) -- persistent user memory CRUD
- **Node Liveness** (`app/services/node_liveness.py`) -- refreshes `last_seen` from any proof-of-life channel

## Node Online Status

A node is shown as **Online** in the admin dashboard when its `last_seen` timestamp is within the past 15 minutes (`Node.is_online()` in `app/models.py`).

### How `last_seen` is refreshed

Since jarvis-command-center#17 (June 2026), `last_seen` is updated by **any authenticated node interaction**, not just the dedicated HTTP heartbeat. This means a node that is actively serving voice commands or MQTT requests stays marked online even if its heartbeat POSTs are failing (e.g. over a flaky WAN or Cloudflare tunnel).

| Interaction | Refresh mechanism |
|-------------|-------------------|
| Any node-authenticated HTTP request — voice, `/continue`, `conversation/start`, results callbacks | `touch_node_last_seen()` called in `verify_api_key` |
| Successful MQTT request/response round-trip | `record_node_seen()` called after `_mqtt_request` returns |
| Dedicated heartbeat (`POST /admin/nodes/heartbeat`, every 300 s) | Unchanged — still runs and also updates `version`, `busy`, and `protocols` fields |

All liveness updates are **best-effort**: they never raise into an auth path or request handler, and a DB error during a liveness write is swallowed and logged at DEBUG level.

### Online threshold

`Node.is_online()` returns `True` when `last_seen >= now − 15 min`. A node that has not interacted with Command Center on any channel for 15 minutes is considered offline.

### Write debounce

`touch_node_last_seen` skips the DB write if `last_seen` was already updated within the last 60 seconds. This keeps writes bounded on busy paths (at most ~1 write/minute/node from the hot path) while keeping liveness well within the 15-minute threshold.

## MQTT Broker Auth (Transition)

Added in jarvis-command-center#33. Steps 2–3 of the broker-auth rollout: command-center can now authenticate to the MQTT broker itself, and hands the same shared credential to authenticated nodes. Both changes are **inert until broker auth is actually enabled** on the broker (still anonymous-allowed today), so this ships ahead of the broker config + node-side changes with no behavior change on current installs.

- **`mqtt_client`** reads a shared broker credential from `MQTT_USERNAME` / `MQTT_PASSWORD` and calls `username_pw_set()` before connecting. Unset (today's default) → connects anonymously exactly as before.
- **`GET /api/v0/node/mqtt-credentials`** (node `X-API-Key` auth) hands the authenticated node the shared credential over its already-trusted HTTP channel — never over MQTT itself, which would be circular. Returns `{"username": null, "password": null}` while unset, so the node stays anonymous until the broker is actually locked down.

**Rollout sequence:**

1. Command-center authenticates + serves credentials (this PR) — inert until env vars are set.
2. Admin generates the broker password file. Since jarvis-admin#27 / jarvis-installer#18 (P0.4), **fresh** installs generate the broker locked (`MQTT_ALLOW_ANON=false`) from first boot — see [Admin: MQTT Broker Lock](admin.md#mqtt-broker-lock-fresh-installs). Installs upgrading from a pre-P0.4 `.env` still get the transition window (`allow_anonymous true`) unless already migrated.
3. Node fetches + uses the credential, with an anonymous fallback.
4. Operator on an upgraded (pre-P0.4) fleet flips `allow_anonymous false` on the broker once all clients have adopted the credential; fresh installs are already locked and need no operator action.

## Web Search

Added in jarvis-command-center#20. The command center exposes two outbound-web **server tools** that let Jarvis answer queries using live internet data:

| Tool | Behaviour |
|---|---|
| `quick_search` | Synchronous live lookup — sources are fetched and injected into the LLM context before the answer is generated. |
| `deep_research` | Asynchronous background research — results are delivered via push notification and the user's inbox. |

### Gate — `web_search.enabled`

Both tools are gated behind the per-household `web_search.enabled` DB setting (**default `false`, fail-closed**). When disabled:

- The tools are excluded from the warmup tool whitelist — the model is never offered them and their prompt guidance drops out automatically.
- The fast-stream path blocks `quick_search` predictions regardless of classifier confidence.
- Defense-in-depth re-checks at `execute()` time reject any hallucinated call.

**Fail-closed:** any settings error (DB down, missing key) resolves to `false`. Web search is never accidentally enabled by an outage — the opposite of the memory gate, which fails open.

Household admins toggle the setting from **Household Settings** in the mobile app (see [Mobile Household Settings API](#mobile-household-settings-api) above). It can also be set via **Admin → Settings → web_search** in the command-center admin UI.

### Jina Reader Proxy — `web_scraping.allow_external`

Added in jarvis-command-center#22. Deep research may encounter pages that reject direct fetches (paywalls, bot-blocks). The web scraper can fall back to the public **r.jina.ai** reader proxy, but that proxy receives the target URL — egress to a third party.

This fallback is an independent per-household gate, **`web_scraping.allow_external`** (**default `false`, fail-closed**):

- `false` (default): deep research fails closed on hard-to-fetch pages — no URLs leave the household network via Jina.
- `true`: the Jina fallback is enabled for that household. Pages that cannot be fetched directly are sent to r.jina.ai.

Household admins toggle this from **Household Settings** in the mobile app (same screen as `web_search.enabled`). Enabling `web_search.enabled` alone does **not** enable the Jina fallback — these are independent gates.

**Fail-closed:** any settings error → treated as `false`.

### Voice-Only Limitation

Web search is **voice-only today**. The mobile/web chat path routes every tool call to the node over MQTT and never executes command-center server tools in-process, so `quick_search` and `deep_research` do not work in the chat UI. Making web search work in chat requires teaching the chat path to execute server tools locally (distinguishing server tools from node tools) — a separate piece of work.

### Double-Egress Gotcha

The `web_search.enabled` gate controls **server tools only**. The legacy `jarvis-cmd-web-search` node plugin (if installed on a node) is merged into the warmup prompt and routed directly to the node — it is **not** governed by this setting. "Disable web search = zero outbound egress" only holds if that plugin is not installed. Check the node's installed plugins if strict no-egress is required.

## Update Checks

Added in jarvis-command-center#22. When a node update is triggered, the command center can look up the latest node-setup release on GitHub (`api.github.com`) to resolve the "latest" target version. This outbound lookup is gated behind a global `updates.allow_check` setting (**default `false`, fail-closed**).

### Gate — `updates.allow_check`

- `false` (default): no outbound request to api.github.com. Requests for the "latest" version return `None`; the node-update endpoint returns `503` if no explicit version was provided.
- `true`: version lookups to `api.github.com/repos/alexberardi/jarvis-node-setup/releases/latest` are permitted.

**Fail-closed:** any settings error → treated as `false`; no outbound GitHub egress.

**Explicit versions bypass the gate:** providing a specific version (e.g. `v0.3.1`) to the node-update endpoint never touches GitHub — it installs that exact version regardless of `updates.allow_check`.

**Scope:** global (not per-household). The update-check call site is unauthenticated in the JWT/household sense, so this is a box-level toggle set via **Admin → Settings → updates**.

## Node Task Status Reporting

Added in jarvis-command-center#35. Nodes can self-report a terminal status for their own tasks via `POST /api/v0/nodes/tasks/{task_id}/status` (node `X-API-Key` auth) — introduced so a node's `allow_updates` consent-gate refusal (see [node-setup: Update Policy](../clients/node-setup.md#update-policy)) surfaces immediately instead of dying ~15 minutes later as a misleading sweeper "no heartbeat" timeout.

**Behaviour:**

- A node may only fail **its own** `kind="update"` tasks — cross-node, wrong-kind, and unknown task IDs all return the same 404, so task IDs cannot be enumerated.
- State is whitelisted to `failed` (a `Literal`, not a free string) — success is still inferred only from the post-upgrade heartbeat version, so a node cannot self-report a completed update.
- Terminal-state immutability is enforced with a conditional `UPDATE` (not check-then-write), so this can never race the 2-minute sweeper or the cancel endpoint into clobbering an existing terminal state (e.g. "Cancelled by user").

A node posting to an older command center that predates this endpoint gets a swallowed 404; the sweeper timeout remains the backstop in that case. The mobile app renders `task.error_message` verbatim on failure, so no separate mobile-side change was needed to surface the reason.

## Secret Boot Guard (`ADMIN_API_KEY` / `JARVIS_AUTH_SECRET_KEY`)

Added in jarvis-command-center#37, closing the last fail-open-default gap in the audit's H2 family (mirrors jarvis-auth's `settings.enforce_secret_security` and jarvis-notifications' `validate_security`). Previously `.env.example` shipped `ADMIN_API_KEY=change-me` and `verify_admin_key` accepted it as valid — it only failed closed when the var was completely unset.

On startup, `enforce_secret_security()` checks `ADMIN_API_KEY` and `JARVIS_AUTH_SECRET_KEY` against a placeholder list (`change-me`, `changeme`, `change_me`, `__set_me__`, plus the verbatim `env.template` values, case-insensitive) and a 16-character minimum length:

- **Empty, placeholder, or too short:** always logs a loud warning. **Fatal (startup aborts)** only when `JARVIS_ENV=production`. Dev boots and compose-mode installs that don't set `JARVIS_ENV` are unaffected.
- **Strong values:** silent, no warning.

`.env.example` now ships `ADMIN_API_KEY=__SET_ME__` instead of `change-me` (still caught by the guard if copied verbatim). `JARVIS_APP_KEY` and similar outbound-credential vars are intentionally **not** covered — those are credentials command-center *presents* to other services, not ones it validates locally, so a weak value there doesn't fail open the same way.

**To harden a production deploy:** set `JARVIS_ENV=production` and generate strong values with `openssl rand -hex 32` for both `ADMIN_API_KEY` and `JARVIS_AUTH_SECRET_KEY`.

## not_for_me Detection

The command center uses a `<not_for_me/>` sentinel in LLM responses to reject transcripts that were not directed at Jarvis. Since jarvis-command-center#11, the classification behavior is conditional on the direction hint the node ships with each transcript.

### Direction Hints

The node's pre-wake VAD window (~5 s) generates a `[direction hint:]` line included with each transcript. Values:

| Hint | Meaning |
|------|---------|
| (absent) | Room state unknown |
| quiet / directed | Speech was the first sound after silence — likely a deliberate address |
| ambient / overheard | Continuous room conversation was already underway when the wake word fired |

### Borderline Case Policy

`NOT_FOR_ME_INSTRUCTION` in `app/core/prompt_providers/shared/core_rules.py` branches on the hint:

| Direction hint | Borderline policy |
|----------------|-------------------|
| None or quiet | **Answer.** Vague phrasing, unusual word choice, a short "thanks" or "never mind" all count as addressed to Jarvis. `<not_for_me/>` is reserved for clear ambient capture, not for ambiguous requests. |
| Ambient / overheard | **Silence.** Without explicit addressing ("Jarvis …", "hey assistant …") or a clear imperative or question, emit `<not_for_me/>`. The node has already done the acoustic work; the prompt defers to that signal on borderline transcripts. |

### Paired Node Behavior

When the command center responds with `<not_for_me/>`, the node holds its wake gate closed for a configurable cool-down (default 20 s, controlled by `not_for_me_quiet_seconds` in the node's `config.json`). This prevents the next sentence of the same side conversation from re-triggering wake. See the [node-setup Wake Behavior](../clients/node-setup.md#wake-behavior) section for details.

## Key Settings (DB-driven)

These settings are persisted in PostgreSQL and editable via **Admin → Settings** in the admin UI without restarting the service.

| Key | Default | Description |
|---|---|---|
| `web_search.enabled` | `false` (per-household) | Master toggle for `quick_search` + `deep_research`. Fail-closed. See [Web Search](#web-search). |
| `web_scraping.allow_external` | `false` (per-household) | Opt-in gate for the r.jina.ai reader-proxy fallback in deep research. Fail-closed. Household-admin controllable via mobile. See [Jina Reader Proxy](#jina-reader-proxy-web_scrapingallow_external). |
| `updates.allow_check` | `false` (global) | Allow outbound version lookups to api.github.com for node release checks. Explicit version installs bypass this gate. Fail-closed. See [Update Checks](#update-checks). |
| `phone_calls.enabled` | `false` (per-household) | Master toggle for the `make_phone_call` tool. Fail-closed — a disabled tool speaks an honest refusal instead of dialing. See [Phone Calls](#phone-calls). |


## Prompt Providers

Command-center selects a prompt provider to build the system prompt and (for native-tool-calling providers) prepare tool schemas for the API. The active provider is chosen by the `llm.interface` config-service DB setting or the `JARVIS_SYSTEM_PROMPT_PROVIDER` env var override.

| Provider | `supports_native_tools` | `use_tool_classifier` | Best for |
|----------|------------------------|----------------------|---------|
| `JarvisModel` | `False` | `True` | Local GGUF / MLX / vLLM — text `<tool_call>` parsing + fastText pre-routing |
| `ChatGPTOpenAI` | `True` | `False` | OpenAI-compatible cloud models (e.g. `gpt-4.1-nano`) via the REST backend |

### ChatGPTOpenAI

Added in jarvis-command-center#14. The first provider with `supports_native_tools=True` — command-center's native tool-calling path was previously unused end-to-end.

**How it differs from text-based providers:**

- Tools are forwarded to the model via the OpenAI `tools` API parameter with `tool_choice="auto"`. The model returns structured `tool_calls`; command-center reads them directly instead of parsing `<tool_call>` text tags.
- The system prompt is deliberately **concise** — tool schemas are delivered natively, so they are not embedded in the cached system prompt (avoids token waste and llama.cpp prefix-cache invalidation).
- `use_tool_classifier = False` — a capable cloud model routes from the native schemas; fastText hints are not needed and are skipped.

**To activate** (pair with the REST backend — see [llm-proxy REST backend](llm-proxy.md#rest-remote-api-proxy)):

```bash
# Config-service DB setting (preferred)
llm.interface = ChatGPTOpenAI

# Or override via environment variable
JARVIS_SYSTEM_PROMPT_PROVIDER=ChatGPTOpenAI
```

Full REST backend setup for `gpt-4.1-nano`:

```bash
JARVIS_LIVE_MODEL_BACKEND=REST
JARVIS_LIVE_REST_MODEL_URL=https://api.openai.com
JARVIS_REST_PROVIDER=openai
JARVIS_REST_MODEL_NAME=gpt-4.1-nano
JARVIS_REST_AUTH_TYPE=bearer
JARVIS_REST_AUTH_TOKEN=sk-your-key
JARVIS_SYSTEM_PROMPT_PROVIDER=ChatGPTOpenAI
```


## Environment Variables

### Core

| Variable | Description |
|----------|-------------|
| `DB_URL` | PostgreSQL connection string (must point to a pgvector-enabled instance) |
| `MIGRATIONS_DATABASE_URL` | PostgreSQL connection string for Alembic migrations |
| `PORT` | API port (default `7703`) |
| `ADMIN_API_KEY` | API key for admin endpoints. Placeholder/short values are rejected at boot in production — see [Secret Boot Guard](#secret-boot-guard-admin_api_key-jarvis_auth_secret_key) |

### Authentication

| Variable | Description |
|----------|-------------|
| `JARVIS_AUTH_APP_ID` | App identity for service-to-service auth (default `command-center`) |
| `JARVIS_AUTH_APP_KEY` | App key for service-to-service auth |
| `JARVIS_AUTH_SECRET_KEY` | JWT secret key — must match `AUTH_SECRET_KEY` in jarvis-auth. Required for mobile app JWT validation. Placeholder/short values are rejected at boot in production — see [Secret Boot Guard](#secret-boot-guard-admin_api_key-jarvis_auth_secret_key) |
| `NODE_AUTH_CACHE_TTL` | Auth validation cache TTL in seconds (default `60`) |

### MQTT Broker Auth

| Variable | Description |
|----------|-------------|
| `MQTT_USERNAME` | Shared MQTT broker username. Unset (default) → command-center connects to the broker anonymously and `/api/v0/node/mqtt-credentials` returns `null`. See [MQTT Broker Auth](#mqtt-broker-auth-transition). |
| `MQTT_PASSWORD` | Shared MQTT broker password, paired with `MQTT_USERNAME`. |

### Service Discovery

| Variable | Description |
|----------|-------------|
| `JARVIS_CONFIG_URL` | Config service URL (default `http://localhost:7700`) |

### LLM Proxy

| Variable | Description |
|----------|-------------|
| `JARVIS_LLM_PROXY_API_VERSION` | LLM proxy API version (default `1`) |
| `JARVIS_MODEL_INTERFACE` | Model interface class: `JarvisAdapterModel` or `JarvisModel` |
| `JARVIS_SMALL_MODEL_MODE` | Use smaller/faster model for real-time responses (`True`) |

### Tool Classifier (fastText router)

The command center uses a fastText model to pre-route commands to the right tool before hitting the LLM, reducing latency.

| Variable | Description |
|----------|-------------|
| `JARVIS_TOOL_CLASSIFIER_ENABLED` | Enable the fastText tool classifier (`True`) |
| `JARVIS_TOOL_CLASSIFIER_MODEL_PATH` | Path to the compiled `.bin` classifier model |
| `JARVIS_TOOL_CLASSIFIER_EXTRA_TRAINING_PATH` | Path to additional JSONL training data |
| `JARVIS_TOOL_CLASSIFIER_MIN_CONFIDENCE` | Minimum confidence to use classifier result (default `0.6`) |
| `JARVIS_TOOL_ROUTER_FILTER_MIN_CONFIDENCE` | Minimum confidence to include a tool in the candidate list (default `0.85`) |

### Prompt Configuration

| Variable | Description |
|----------|-------------|
| `JARVIS_SYSTEM_PROMPT_PROVIDER` | Active prompt provider class (see [Prompt Providers](#prompt-providers)). Example: `ChatGPTOpenAI` |
| `JARVIS_PARAMETER_INFERENCE_PROMPT_PROVIDER` | Override the parameter inference prompt provider class |
| `JARVIS_TRANSCRIPTION_CLEANUP_ENABLED` | Apply LLM-based cleanup to raw transcription before routing (`False`) |
| `JARVIS_PROMPT_INCLUDE_ANTIPATTERNS` | Include anti-pattern examples in the system prompt (`True`) |
| `JARVIS_PROMPT_INCLUDE_PARAM_DESCRIPTIONS` | Include parameter descriptions in the system prompt (`True`) |

### OAuth

| Variable | Description |
|----------|-------------|
| `JARVIS_EXTERNAL_URL` | External URL used as the OAuth callback base (e.g. `https://jarvis.yourdomain.com`). Falls back to request headers if unset. |
| `JARVIS_TOKEN_ENCRYPTION_KEY` | 32-byte hex key for AES-256-GCM encryption of stored OAuth tokens. Falls back to `SHA-256(SECRET_KEY)` if unset. |

### Logging

| Variable | Description |
|----------|-------------|
| `JARVIS_APP_ID` | App identity for centralized logging (default `command-center`) |
| `JARVIS_APP_KEY` | App key for centralized logging |
| `JARVIS_LOG_CONSOLE_LEVEL` | Console log level (default `INFO`) |
| `JARVIS_LOG_REMOTE_LEVEL` | Remote log level sent to jarvis-logs (default `DEBUG`) |

## Dependencies

- **PostgreSQL** (`pgvector/pgvector:pg16` required) -- nodes, memories, command history. Alembic migration `e9f0a1b2c3d4` runs `CREATE EXTENSION IF NOT EXISTS vector` and adds a `vector(384)` embedding column with an HNSW index on `user_memories`. Stock `postgres:16` does not ship the `vector` extension and will abort on fresh install with `extension "vector" does not exist`. Use `pgvector/pgvector:pg16` (drop-in for `postgres:16`). The installer and generated `docker-compose.prod.yaml` both use this image automatically. Bumped from `pg15` in jarvis-command-center#39 to align with jarvis-installer (the source of truth); pg15 and pg16 data directories are **not** compatible — existing installs upgrading from pg15 must migrate first, see the [pg15 → pg16 migration guide](https://github.com/alexberardi/jarvis-command-center/blob/main/docs/postgres-pg15-to-pg16-migration.md).
- **jarvis-auth** -- node auth and app-to-app auth
- **jarvis-config-service** -- service discovery
- **jarvis-llm-proxy-api** -- LLM inference for intent parsing
- **jarvis-logs** -- structured logging
- **jarvis-whisper-api** -- speech-to-text (optional, for audio input)
- **jarvis-notifications** -- push notifications for deep research results (optional)
- **jarvis-tts** -- text-to-speech (optional)
- **jarvis-web-scraper** -- web content extraction for deep research (optional)
- **jarvis-phone-gateway** -- dials and runs the live call for `make_phone_call` (optional; see [Phone Calls](#phone-calls) and [Phone Gateway](phone-gateway.md))

## Dependents

- **jarvis-node-setup** -- Pi Zero voice nodes send commands here
- **jarvis-node-mobile** -- mobile app sends commands here

## Impact if Down

No voice commands are processed. Nodes cannot submit audio or text for processing. All command routing, memory, and speaker identification is unavailable.
