# Services

Jarvis is composed of small, focused microservices. Each runs as a Docker container (or locally for GPU-dependent workloads on macOS) and communicates over HTTP with app-to-app authentication.

## Service Inventory

| Service | Port | Description | Tier |
|---------|------|-------------|------|
| [Config Service](config-service.md) | 7700 | Service discovery hub | 0 - Foundation |
| [Auth](auth.md) | 7701 | JWT authentication, app-to-app auth | 1 - Core Infra |
| [Logs](logs.md) | 7702 | Centralized logging via Loki/Grafana | 1 - Core Infra |
| [Command Center](command-center.md) | 7703 | Voice command orchestrator | 2 - Command Processing |
| [LLM Proxy](llm-proxy.md) | 7704/7705 | LLM inference (MLX/GGUF/vLLM) | 2 - Command Processing |
| [Whisper API](whisper-api.md) | 7706 | Speech-to-text via whisper.cpp | 3 - Specialized |
| [TTS](tts.md) | 7707 | Text-to-speech via Piper | 3 - Specialized |
| [OCR Service](ocr-service.md) | 7031 | OCR with multiple backends | 3 - Specialized |
| [Recipes Server](recipes-server.md) | 7030 | Recipe CRUD and meal planning | 3 - Specialized |
| [Notifications](notifications.md) | 7712 | Push notifications and inbox | 3 - Specialized |
| [Settings Server](settings-server.md) | 7708 | Settings aggregator | 4 - Management |
| [MCP](mcp.md) | 7709 | Claude Code integration | 4 - Management |
| [Admin](admin.md) | 7710 | Web admin UI | 5 - Clients |

## Dependency Tiers

Services are organized into tiers based on how foundational they are:

- **Tier 0 (Foundation)** -- Must be running for anything to work. Config Service and PostgreSQL.
- **Tier 1 (Core Infrastructure)** -- Auth and Logs. Most services depend on auth; logs degrade gracefully.
- **Tier 2 (Command Processing)** -- Command Center and LLM Proxy. The voice command pipeline.
- **Tier 3 (Specialized)** -- Domain services (whisper, TTS, OCR, recipes, notifications). Each is independently optional.
- **Tier 4 (Management)** -- Settings, MCP, admin tools. Used for configuration and development.
- **Tier 5 (Clients)** -- End-user interfaces (admin web UI, mobile app, Pi nodes).

## Dependency Graph

```mermaid
graph TD
    subgraph "Tier 0 - Foundation"
        CONFIG[Config Service<br/>7700]
        PG[(PostgreSQL)]
        REDIS[(Redis)]
        MINIO[(MinIO)]
    end

    subgraph "Tier 1 - Core Infrastructure"
        AUTH[Auth<br/>7701]
        LOGS[Logs<br/>7702]
    end

    subgraph "Tier 2 - Command Processing"
        CC[Command Center<br/>7703]
        LLM[LLM Proxy<br/>7704/7705]
    end

    subgraph "Tier 3 - Specialized"
        WHISPER[Whisper API<br/>7706]
        TTS[TTS<br/>7707]
        OCR[OCR Service<br/>7031]
        RECIPES[Recipes Server<br/>7030]
        NOTIF[Notifications<br/>7712]
    end

    subgraph "Tier 4 - Management"
        SETTINGS[Settings Server<br/>7708]
        MCP[MCP<br/>7709]
        ADMIN[Admin<br/>7710]
    end

    %% Tier 0 dependencies
    AUTH --> PG
    AUTH --> LOGS
    CONFIG --> PG
    CONFIG --> LOGS

    %% Tier 2
    CC --> AUTH
    CC --> CONFIG
    CC --> LOGS
    CC --> LLM
    CC --> PG

    %% Tier 3
    WHISPER --> AUTH
    WHISPER --> LOGS
    TTS --> AUTH
    TTS --> LOGS
    TTS --> LLM
    OCR --> AUTH
    OCR --> LOGS
    OCR --> REDIS
    RECIPES --> AUTH
    RECIPES --> LOGS
    RECIPES --> PG
    RECIPES --> OCR
    NOTIF --> AUTH
    NOTIF --> CONFIG
    NOTIF --> LOGS
    NOTIF --> PG

    %% Tier 4
    SETTINGS --> CONFIG
    SETTINGS --> AUTH
    MCP --> CONFIG
    MCP --> LOGS
    MCP --> AUTH
    ADMIN --> CONFIG
    ADMIN --> AUTH
    ADMIN --> SETTINGS

    %% Optional edges (dashed)
    CC -.-> WHISPER
    CC -.-> NOTIF
    CC -.-> TTS
```

## Critical Path: Voice Commands

For end-to-end voice commands to work, these services must be running:

1. **Config Service** (service discovery)
2. **Auth** (node and app-to-app authentication)
3. **Command Center** (voice orchestration)
4. **LLM Proxy** (intent parsing and response generation)
5. *Whisper API* (speech-to-text, if using server-side transcription)
6. *TTS* (voice responses, optional)
7. *Logs* (optional, services degrade gracefully to console logging)

## Communication Patterns

All inter-service communication uses HTTP. See [Authentication](../architecture/authentication.md) for details on the three auth modes:

- **App-to-app auth**: `X-Jarvis-App-Id` + `X-Jarvis-App-Key` headers
- **Node auth**: `X-API-Key` header (node_id:node_key)
- **User auth**: `Authorization: Bearer <jwt>` header
