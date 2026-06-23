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
