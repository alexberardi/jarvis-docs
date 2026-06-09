# Pi Zero Node (jarvis-node-setup)

The Pi Zero node is the primary voice interface for Jarvis. It runs on Raspberry Pi Zero hardware (or any Linux/macOS machine for development) with a microphone and speaker attached.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-node-setup/main/install.sh | sudo bash
```

This installs to `/opt/jarvis-node`, sets up a systemd service, and configures audio. After install, pair the node with your server using the mobile app or `authorize_node.py`.

Flags:

| Flag | Description |
|------|-------------|
| `--no-audio` | Skip ALSA / I2S DAC configuration |
| `--force` | Reinstall even if already at latest version |
| `--version TAG` | Install a specific version (e.g. `v0.1.0`) |

## What It Does

1. **Wake word detection** -- Listens locally for a configured wake word using [openWakeWord](https://github.com/dscripka/openWakeWord). No audio leaves the device until the wake word is heard.
2. **Audio capture** -- Records speech until silence is detected.
3. **Command submission** -- Sends the audio to the command center, which handles transcription, intent classification, and command execution.
4. **Response playback** -- Receives spoken responses via MQTT (from the TTS service) and plays them through the speaker.

## Architecture

```
jarvis-node-setup/
├── scripts/
│   └── main.py                # Entry point
├── core/
│   ├── ijarvis_command.py     # Command interface (re-exports from SDK)
│   ├── ijarvis_parameter.py   # Parameter definitions
│   ├── ijarvis_secret.py      # Secret definitions
│   ├── command_response.py    # Response structure
│   └── platform_abstraction.py # Hardware abstraction
├── commands/                  # Built-in commands (control_node, etc.)
├── agents/                    # Background agents (reminders, device discovery)
├── services/
│   ├── secret_service.py      # Encrypted secret management
│   ├── mqtt_tts_listener.py   # MQTT TTS listener
│   ├── agent_scheduler_service.py  # Background agent scheduling
│   ├── alert_queue_service.py # Proactive alert queue + button announce
│   ├── button_service.py      # ReSpeaker GPIO17 button handler
│   ├── settings_snapshot_service.py # Settings snapshot builder
│   └── reminder_service.py    # Persistent reminders
├── stt_providers/
│   └── jarvis_whisper_client.py  # Whisper API client
├── provisioning/              # Headless provisioning system
└── utils/
    ├── audio_volume.py        # PulseAudio volume/mute control
    └── config_service.py      # Configuration loader
```

## Threading Model

The node runs multiple supervised threads:

- **Main thread** -- Voice listener. Detects wake word, captures audio, sends to command center.
- **MQTT thread** -- Receives TTS audio from the broker and plays it through the speaker.
- **Agent scheduler** -- Runs background agents on configurable intervals (reminders, device discovery, token refresh).
- **ButtonShortPress thread** -- Handles ReSpeaker GPIO17 short-press events. Speaks queued alerts via local TTS without blocking the GPIO callback. Started after TTS, LED, and alert-queue services are ready.

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

### Installing Commands from the Pantry

Additional commands can be installed from the community Pantry store via the mobile app or CLI:

```bash
jarvis pantry install get_weather
```

## Built-in Commands

### `control_node` — Volume and Mute

The `control_node` command handles local volume and mute control. It uses pre-routing (no LLM round-trip) for all volume intents.

| Action | Trigger phrases | Notes |
|--------|----------------|-------|
| Volume up | "volume up", "louder", "crank it up", "turn it up" | +10 percentage points |
| Volume down | "volume down", "quieter", "softer", "turn it down" | −10 percentage points |
| Set volume | "set volume to 50", "volume 7", "volume 75%" | N ≤ 10 maps to N×10%; N > 10 is literal % |
| Mute | "mute", "mute the speaker", "please mute" | |
| Unmute | "unmute", "unmute the volume" | |

Volume state is persisted to `config.json` under `volume_percent` and restored on restart. Adjustments apply to both the system default sink and any paired Bluetooth sinks simultaneously.

## Audio

The node uses **PulseAudio** for playback and mute control. The wake-word capture path uses ALSA `dsnoop` directly to avoid PulseAudio resampling and AGC latency.

!!! warning "ALSA softvol removed"
    The `SoftMaster` softvol layer used in HiFiBerry-era setups has been removed. Do not add `amixer sset SoftMaster` calls to install scripts or cron jobs — that control no longer exists.

### PulseAudio Volume Control

Runtime volume and mute go through `pactl`:

- **Set volume**: `pactl set-sink-volume @DEFAULT_SINK@ <percent>%`
- **Toggle mute**: `pactl set-sink-mute @DEFAULT_SINK@ toggle`
- All `bluez_sink.*` Bluetooth sinks are adjusted simultaneously with the default sink.

### ALSA Configuration (`/etc/asound.conf`)

The installer writes an asymmetric config that routes playback through PulseAudio while keeping capture on the raw hardware device:

```
pcm.output         type pulse          — playback via PulseAudio
pcm.dsnoopmic_hw   type dsnoop         — shared capture on hw:seeed2micvoicec,0
                                          ipc_key 87654321, 2ch, 48000 Hz, S16_LE
pcm.dsnoopmic      type plug → dsnoopmic_hw
pcm.!default       type asym: playback=output, capture=dsnoopmic
```

Wake-word detection reads from `dsnoopmic` (raw PCM, no PA resampling). TTS and streaming playback go through PulseAudio.

### Required Systemd Environment

PulseAudio requires `XDG_RUNTIME_DIR` to find its session socket. Add these lines to `/etc/systemd/system/jarvis-node.service`:

```ini
[Service]
User=pi
Group=pi
Environment=HOME=/home/pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
```

Without `XDG_RUNTIME_DIR`, `libpulse` cannot locate the PulseAudio socket and all audio operations will fail silently.

## Hardware: ReSpeaker 2-Mics HAT v2

The node has first-class support for the [Seeed Studio ReSpeaker 2-Mics Pi HAT v2](https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT/). When the HAT is present, the ALSA card appears as `seeed2micvoicec` and the node exposes a `hardware` block in the settings snapshot.

### Hardware Settings Snapshot Block

The `hardware` key appears in every settings snapshot. The mobile app uses it to show or hide HAT-specific controls (LED brightness, button config):

| Field | Type | Description |
|-------|------|-------------|
| `hat_detected` | bool | `true` when ReSpeaker HAT is present |
| `led_chain_available` | bool | `true` when the APA102 LED ring is available (equals `hat_detected`) |
| `audio_card` | string \| null | ALSA card name, e.g. `"seeed2micvoicec"`; `null` on macOS or no HAT |
| `is_muted` | bool | Current PulseAudio mute state; omitted if indeterminate |
| `button_available` | bool | `true` when gpiozero is importable and `hat_detected` is `true` |

### LED Behavior

LED state is persisted in `config.json` (`led_enabled`, `led_brightness_percent`) and applied at startup before the alert queue is wired, so the LED no longer flickers at full brightness on boot.

### Button Behavior

The ReSpeaker GPIO17 button short-press speaks any queued proactive alerts via local TTS and flushes the alert queue. If no alerts are queued it announces "No new notifications." A long-press (hold) still reaches the shutdown handler.

## Dependencies

| Library | Purpose |
|---------|---------|
| PyAudio, SoundDevice | Audio capture and playback |
| paho-mqtt | MQTT integration (TTS listener) |
| openwakeword | Wake word detection |
| httpx | REST client to command center |
| SQLAlchemy + pysqlcipher3 | Local encrypted database |
| jarvis-command-sdk | Shared command/agent interfaces |
| mpv | Streaming command audio playback (`--ao=alsa` path) |

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
| `release_track` | Update channel: `"stable"` (default) or `"dev"` |
| `volume_percent` | Persisted speaker volume (0–100); written on every volume command |
| `led_enabled` | Whether the LED ring is active on boot (HAT nodes only) |
| `led_brightness_percent` | LED brightness applied at startup (0–100, default 100) |

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

## Service User

The node runs as the `pi` user (not `root`). Running as root breaks the PulseAudio session socket path (`XDG_RUNTIME_DIR=/run/user/1000` is only valid for a user with UID 1000).

For nodes originally installed as root, migrate with these steps:

```bash
# 1. Add pi to the bluetooth group
sudo usermod -aG bluetooth pi

# 2. Copy node data to pi's home and fix ownership
sudo cp -a /root/.jarvis /home/pi/.jarvis
sudo chown -R pi:pi /home/pi/.jarvis
sudo chown -R pi:pi /opt/jarvis-node

# 3. Update the systemd unit
sudo sed -i '/\[Service\]/a User=pi\nGroup=pi\nEnvironment=HOME=/home/pi\nEnvironment=XDG_RUNTIME_DIR=/run/user/1000' \
  /etc/systemd/system/jarvis-node.service

# 4. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart jarvis-node
```

!!! tip "Backup before migrating"
    `sudo tar -czf /tmp/jarvis-pre-migration.tar.gz /root/.jarvis /opt/jarvis-node` before step 2.

## Service Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| Command Center (7703) | Yes | Voice command processing |
| TTS (7707) | No | Spoken responses via MQTT |
| Config Service (7700) | No | Service discovery |
