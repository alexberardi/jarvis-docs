# Command Center

The command center is the voice command orchestrator. It receives transcribed text (or raw audio) from nodes, routes it through the LLM for intent parsing and tool selection, executes the appropriate command, and returns the response. It also manages node registration, user memories, and speaker identification.

## Quick Reference

| | |
|---|---|
| **Port** | 7703 |
| **Health endpoint** | `GET /api/v0/health` |
| **Source** | `jarvis-command-center/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL (pgvector required — see Dependencies) |
| **Tier** | 2 - Command Processing |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v0/health` | Health check |
| `POST` | `/api/v0/command` | Process a voice command (text or audio) |
| `POST` | `/api/v0/nodes/register` | Register a new node (admin) |
| `GET` | `/api/v0/nodes` | List registered nodes |
| `GET` | `/api/v0/memories` | List user memories |
| `POST` | `/api/v0/memories` | Create a user memory |
| `DELETE` | `/api/v0/memories/{id}` | Delete a user memory |

For mobile data-browser routes see [Mobile Command-Data API](#mobile-command-data-api) below.

For household settings routes (e.g. web search toggle) see [Mobile Household Settings API](#mobile-household-settings-api) below.

## Mobile Command-Data API

The mobile app manages command records through a set of REST routes that proxy to the node's MQTT data-browser protocol. All routes require a valid mobile JWT.

| Method | Path | Description |
|--------|------|-------------|
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

## Key Components

- **Prompt Engine** (`app/core/prompt_engine.py`) -- builds system prompts with speaker context and memories
- **Tool Parser** (`app/core/tool_parser.py`) -- extracts tool calls from LLM responses
- **Tool Executor** (`app/core/tool_executor.py`) -- dispatches tool calls to the appropriate service
- **Speaker Resolver** (`app/core/utils/speaker_resolver.py`) -- maps speaker IDs to display names
- **Memory Service** (`app/services/memory_service.py`) -- persistent user memory CRUD

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

### Voice-Only Limitation

Web search is **voice-only today**. The mobile/web chat path routes every tool call to the node over MQTT and never executes command-center server tools in-process, so `quick_search` and `deep_research` do not work in the chat UI. Making web search work in chat requires teaching the chat path to execute server tools locally (distinguishing server tools from node tools) — a separate piece of work.

### Double-Egress Gotcha

The `web_search.enabled` gate controls **server tools only**. The legacy `jarvis-cmd-web-search` node plugin (if installed on a node) is merged into the warmup prompt and routed directly to the node — it is **not** governed by this setting. "Disable web search = zero outbound egress" only holds if that plugin is not installed. Check the node's installed plugins if strict no-egress is required.

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

## Environment Variables

### Core

| Variable | Description |
|----------|-------------|
| `DB_URL` | PostgreSQL connection string (must point to a pgvector-enabled instance) |
| `MIGRATIONS_DATABASE_URL` | PostgreSQL connection string for Alembic migrations |
| `PORT` | API port (default `7703`) |
| `ADMIN_API_KEY` | API key for admin endpoints |

### Authentication

| Variable | Description |
|----------|-------------|
| `JARVIS_AUTH_APP_ID` | App identity for service-to-service auth (default `command-center`) |
| `JARVIS_AUTH_APP_KEY` | App key for service-to-service auth |
| `JARVIS_AUTH_SECRET_KEY` | JWT secret key — must match `AUTH_SECRET_KEY` in jarvis-auth. Required for mobile app JWT validation. |
| `NODE_AUTH_CACHE_TTL` | Auth validation cache TTL in seconds (default `60`) |

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
| `JARVIS_SYSTEM_PROMPT_PROVIDER` | Override the default system prompt provider class |
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

- **PostgreSQL** (`pgvector/pgvector:pg15` required) -- nodes, memories, command history. Alembic migration `e9f0a1b2c3d4` runs `CREATE EXTENSION IF NOT EXISTS vector` and adds a `vector(384)` embedding column with an HNSW index on `user_memories`. Stock `postgres:15` does not ship the `vector` extension and will abort on fresh install with `extension "vector" does not exist`. Use `pgvector/pgvector:pg15` (drop-in for `postgres:15`). The installer and generated `docker-compose.prod.yaml` both use this image automatically.
- **jarvis-auth** -- node auth and app-to-app auth
- **jarvis-config-service** -- service discovery
- **jarvis-llm-proxy-api** -- LLM inference for intent parsing
- **jarvis-logs** -- structured logging
- **jarvis-whisper-api** -- speech-to-text (optional, for audio input)
- **jarvis-notifications** -- push notifications for deep research results (optional)
- **jarvis-tts** -- text-to-speech (optional)
- **jarvis-web-scraper** -- web content extraction for deep research (optional)

## Dependents

- **jarvis-node-setup** -- Pi Zero voice nodes send commands here
- **jarvis-node-mobile** -- mobile app sends commands here

## Impact if Down

No voice commands are processed. Nodes cannot submit audio or text for processing. All command routing, memory, and speaker identification is unavailable.
