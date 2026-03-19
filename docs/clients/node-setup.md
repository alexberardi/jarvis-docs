# Pi Zero Node (jarvis-node-setup)

The Pi Zero node is the primary voice interface for Jarvis. It runs on Raspberry Pi Zero hardware (or any Linux/macOS machine for development) with a microphone and speaker attached.

## What It Does

1. **Wake word detection** -- Listens locally for a configured wake word using [Porcupine](https://picovoice.ai/platform/porcupine/). No audio leaves the device until the wake word is heard.
2. **Audio capture** -- Records speech until silence is detected.
3. **Command submission** -- Sends the audio to the command center (`POST /api/v0/command`), which handles transcription, intent classification, and command execution.
4. **Response playback** -- Receives spoken responses via MQTT (from the TTS service) and plays them through the speaker.

## Architecture

```
jarvis-node-setup/
├── scripts/
│   └── main.py                # Entry point
├── core/
│   ├── ijarvis_command.py     # Command interface (IJarvisCommand)
│   ├── ijarvis_parameter.py   # Parameter definitions
│   ├── ijarvis_secret.py      # Secret definitions
│   ├── command_response.py    # Response structure
│   └── platform_abstraction.py # Hardware abstraction
├── commands/                  # Built-in commands (20+)
│   ├── weather_command.py
│   ├── calculator_command.py
│   ├── jokes_command.py
│   ├── smart_home_command.py
│   └── ...
├── services/
│   ├── secret_service.py      # Encrypted secret management
│   └── mqtt_tts_listener.py   # MQTT TTS listener
├── stt_providers/
│   └── jarvis_whisper_client.py  # Whisper API client
├── provisioning/              # Headless provisioning system
└── utils/
    └── config_service.py      # Configuration loader
```

## Threading Model

The node runs two threads:

- **Main thread** -- Voice listener. Detects wake word, captures audio, sends to command center.
- **Background thread** -- MQTT listener. Receives TTS audio from the broker and plays it through the speaker.

## Plugin Architecture

Commands live in the `commands/` directory. Each command implements the `IJarvisCommand` interface:

```python
class IJarvisCommand(ABC):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> list[IJarvisParameter]: ...

    @property
    def required_secrets(self) -> list[IJarvisSecret]: ...

    def execute(self, request_info: RequestInformation, **kwargs) -> CommandResponse: ...
```

Commands declare their parameters and secrets. The command center uses these schemas to build LLM tool definitions. When the LLM selects a command, the center calls `execute()` with the extracted arguments.

### Pre-Routing (Fast Path)

Commands can implement `pre_route()` to claim short, unambiguous utterances without LLM inference:

```python
def pre_route(self, voice_command: str) -> PreRouteResult | None:
    if voice_command.strip().lower() == "pause":
        return PreRouteResult(arguments={}, spoken_response="Paused.")
    return None
```

This skips the LLM entirely, reducing latency to near-zero for simple commands like "pause" or "stop".

### Installing Commands

```bash
cd jarvis-node-setup

# List all commands and their required secrets
python scripts/install_command.py --list

# Install all commands (runs DB migrations + seeds secrets table)
python scripts/install_command.py --all

# Install a single command
python scripts/install_command.py get_weather
```

## Dependencies

| Library | Purpose |
|---------|---------|
| PyAudio, SoundDevice | Audio capture and playback |
| paho-mqtt | MQTT integration (TTS listener) |
| pvporcupine | Wake word detection |
| httpx | REST client to command center |
| SQLAlchemy + pysqlcipher3 | Local encrypted database |

## Local Encrypted Storage

Node secrets (API keys, OAuth tokens) are stored in a local SQLite database encrypted with [PySQLCipher](https://github.com/niccokunzmann/pysqlcipher3). The encryption key (`K1`) is generated on first boot and stored in `~/.jarvis/secrets.key`.

This means secrets are encrypted at rest on the Pi Zero's SD card.

## Configuration

Development nodes use `config-mac.json` (gitignored). Production nodes use configuration set during provisioning.

Key config fields:

| Field | Description |
|-------|-------------|
| `node_id` | UUID assigned during registration |
| `api_key` | API key for authenticating to command center |
| `command_center_url` | URL of the command center |
| `room` | Room name (e.g., "kitchen", "office") |
| `household_id` | Household UUID for multi-tenant isolation |

## Node Authentication

Nodes authenticate to the command center with an API key header:

```
X-API-Key: {node_id}:{api_key}
```

For development, register a node using the `authorize_node.py` utility:

```bash
python utils/authorize_node.py \
  --cc-key <ADMIN_API_KEY> \
  --household-id <household-uuid> \
  --room office --name dev-mac \
  --update-config config-mac.json
```

## Service Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| Command Center (7703) | Yes | Voice command processing |
| TTS (7707) | No | Spoken responses via MQTT |
| Config Service (7700) | No | Service discovery |
