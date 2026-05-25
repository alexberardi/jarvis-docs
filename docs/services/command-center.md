# Command Center

The command center is the voice command orchestrator. It receives transcribed text (or raw audio) from nodes, routes it through the LLM for intent parsing and tool selection, executes the appropriate command, and returns the response. It also manages node registration, user memories, and speaker identification.

## Quick Reference

| | |
|---|---|
| **Port** | 7703 |
| **Health endpoint** | `GET /api/v0/health` |
| **Source** | `jarvis-command-center/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL |
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

## Environment Variables

### Core

| Variable | Description |
|----------|-------------|
| `DB_URL` | PostgreSQL connection string |
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

- **PostgreSQL** -- nodes, memories, command history
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
