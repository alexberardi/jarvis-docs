# Jarvis Developer Documentation

Jarvis is a fully private, self-hosted voice assistant built on Pi Zero nodes and a microservice backend. This documentation covers everything you need to build custom commands, understand the architecture, and deploy your own instance.

## Why Jarvis?

- **Fully private** — No cloud dependencies. All data stays on your network.
- **Self-hostable** — Same open-source codebase for local and cloud deployments.
- **Extensible** — Add capabilities by implementing a single Python interface.
- **Voice-first** — Wake word detection, speech-to-text, LLM routing, text-to-speech.

## Architecture at a Glance

```mermaid
graph LR
    Node["Pi Zero Node<br/>(mic + speaker)"] -->|voice audio| CC["Command Center"]
    CC -->|audio| Whisper["Whisper API<br/>(speech-to-text)"]
    Whisper -->|text| CC
    CC -->|intent| LLM["LLM Proxy<br/>(tool routing)"]
    LLM -->|tool call| CC
    CC -->|execute| CMD["Your Command<br/>(IJarvisCommand)"]
    CMD -->|result| CC
    CC -->|text| TTS["TTS<br/>(text-to-speech)"]
    TTS -->|audio| Node
```

## Quick Links

| | |
|---|---|
| **[Getting Started](getting-started/index.md)** | Install Jarvis, start services, and send your first voice command. |
| **[Extending Jarvis](extending/index.md)** | The plugin system — commands, agents, device adapters, prompt providers, and more. |
| **[Architecture](architecture/index.md)** | Understand the voice pipeline, service discovery, and authentication patterns. |
| **[Cloud Services](architecture/cloud.md)** | Pantry (command store), Notifications Relay, Web Chat, and the Command SDK. |
| **[Services](services/index.md)** | Reference for every microservice — APIs, configuration, and dependencies. |

## Built-in Commands

Jarvis ships with 20+ commands out of the box:

| Command | Description |
|---------|-------------|
| `get_weather` | Weather conditions and forecasts |
| `calculate` | Arithmetic operations |
| `search_web` | Web search with AI summaries |
| `control_device` | Smart home device control |
| `set_timer` | Timers and alarms |
| `read_calendar` | Calendar queries |
| `send_email` | Email composition and sending |
| `play_music` | Music playback control |
| `tell_joke` | Random jokes |
| ... and more | See the full [command list](commands/index.md) |
