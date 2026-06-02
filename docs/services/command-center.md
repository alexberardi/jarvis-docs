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

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (must point to a pgvector-enabled instance — see Dependencies) |
| `ADMIN_API_KEY` | Admin endpoint protection |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |
| `JARVIS_CONFIG_URL` | Config service URL |

## Dependencies

- **PostgreSQL** (`pgvector/pgvector:pg15`) -- nodes, memories, command history. Must use the pgvector image; stock `postgres:15` does not ship the `vector` extension required by the `e9f0a1b2c3d4` migration (`vector(384)` embedding column + HNSW index on `user_memories`).
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
