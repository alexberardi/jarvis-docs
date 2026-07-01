# Node (jarvis-node-setup)

The Jarvis node is the primary voice interface for Jarvis. It runs on Raspberry Pi hardware (Pi Zero 2 W, Pi 4, Pi 5), any 64-bit Linux machine, or inside Docker with a mic and speaker attached. macOS is supported for development (native only; Docker Desktop has no audio hardware access via VM).

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-node-setup/v0.1.131/install.sh | sudo bash
```

This installs to `/opt/jarvis-node`, sets up a systemd service, and configures audio. After install, pair the node with your server using the mobile app or `authorize_node.py`.

Flags:

| Flag | Description |
|------|-------------|
| `--no-audio` | Skip ALSA / I2S DAC configuration |
| `--force` | Reinstall even if already at latest version |
| `--version TAG` | Install a specific version (e.g. `v0.1.131`) |

## What It Does

1. **Wake word detection** -- Listens locally for a configured wake word using [openWakeWord](https://github.com/dscripka/openWakeWord). Local ONNX inference — no cloud service or API key required. The model is set via `wake_word_model` in `config.json` (default: `hey_jarvis`); models download automatically on first run. No audio leaves the device until the wake word is heard.
2. **Audio capture** -- Records speech until silence is detected.
3. **Command submission** -- Sends the audio to the command center, which handles transcription, intent classification, and command execution.
4. **Response playback** -- Receives spoken responses via MQTT (from the TTS service) and plays them through the speaker.

## Architecture

```
jarvis-node-setup/
├── scripts/
│   ├── main.py                # Native entry point
│   ├── entrypoint.py          # Container entry point (routes setup / voice mode)
│   ├── jarvis-apt-install     # Sudo-able apt-get shim for Pantry-declared packages
│   └── configure-audio.sh     # Audio device auto-detect for containerised runs
├── core/
│   ├── ijarvis_command.py     # Command interface (re-exports from SDK)
│   ├── ijarvis_parameter.py   # Parameter definitions
│   ├── ijarvis_secret.py      # Secret definitions
│   ├── command_response.py    # Response structure
│   └── platform_abstraction.py # Hardware abstraction (Pi vs generic Linux)
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

### Platform detection

`core/platform_abstraction.py` exposes two probes used at runtime:

- `is_raspberry_pi()` — reads the device-tree model string; returns `True` only on Pi hardware.
- `has_respeaker_hat()` — checks for the `seeed2micvoicec` ALSA card; gates TLV320 self-heal and sink keepalive.

On non-Pi 64-bit Linux (and in containers), `LinuxHostAudioProvider` is selected instead of the HAT-specific provider. HAT-specific drivers ship in `requirements-hat.txt` and are not installed by default.

## Threading Model

The node runs multiple supervised threads:

- **Main thread** -- Voice listener. Detects wake word, captures audio, sends to command center.
- **MQTT thread** -- Receives TTS audio from the broker and plays it through the speaker.
- **Agent scheduler** -- Runs background agents on configurable intervals (reminders, device discovery, token refresh).
- **ButtonShortPress thread** -- Handles ReSpeaker GPIO17 short-press events. Speaks queued alerts via local TTS without blocking the GPIO callback. Started after TTS, LED, and alert-queue services are ready.

## Wake Behavior

### Wake Acceptance Gate

A unified gate (`_wake_min_next_ts`) in `scripts/voice_listener.py` controls when the next wake fire is accepted. Two sources push the gate forward:

| Source | Default duration | Trigger |
|--------|-----------------|---------|
| Same-utterance debounce | 8 s | Every accepted wake — prevents openWakeWord from scoring the same "Hey Jarvis" on consecutive 80 ms chunks |
| `not_for_me` cool-down | 20 s (configurable) | When the command center responds with `<not_for_me/>`, side conversations cluster; suppressing for the cool-down kills the re-trigger loop |

Multiple suppressions do not stack — the later or longer deadline wins.

Log lines to watch in `journalctl`:

| Log key | Meaning |
|---------|---------|
| `wake-suppressed-gate` | A wake score > 0.3 was suppressed; includes `cooldown_remaining_sec` |
| `wake-gate-extended` | The gate was pushed further out; includes `seconds` and `reason` |

### Configuring the not_for_me cool-down

Set `not_for_me_quiet_seconds` in `config.json` (default `20.0`). Raise it if side conversations keep looping after a `<not_for_me/>` response; lower it if legitimate follow-ups are being dropped after a misclassification.

```json
{
  "not_for_me_quiet_seconds": 20.0
}
```

### suppress_wake_for() API

Any caller can extend the gate programmatically:

```python
from scripts.voice_listener import suppress_wake_for

suppress_wake_for(seconds=30.0, reason="my-signal")
```

The gate advances only if the new deadline is further out than the current one. The `reason` string appears in `wake-gate-extended` log lines for debuggability.

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

#### Command Installation Pipeline

The install pipeline runs these steps in order: clone → validate → test → copy files → **apt deps (step 9)** → pip deps (step 10) → namespace → secrets → registry enable.

apt runs before pip so a fast failure (disk full, bad package name, missing wrapper) aborts before the slower pip work begins.

#### apt Dependencies

Commands that declare system packages in their manifest (`apt_packages` field) trigger an apt install step. The installer:

1. **Pre-flights disk space** — requires ≥ 500 MB free on `/`. Fails fast before invoking apt if the check fails.
2. **Validates package names** — each name is checked against `^[a-z][a-z0-9.+-]*$`. One invalid name aborts the entire call with no partial installs.
3. **Invokes `/usr/local/sbin/jarvis-apt-install`** via `sudo` — a root-owned POSIX sh wrapper deployed by `install.sh` that forwards valid names to `nice -n 15 apt-get install -y --no-install-recommends` with a 60 s dpkg-lock wait and a 300 s total timeout.

The installer adds this entry to `/etc/sudoers.d/jarvis-node`:

```
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/local/sbin/jarvis-apt-install *
```

The `*` is in the argument position (not the binary path), so only `jarvis-apt-install` itself can be invoked with elevated privileges — no other command gains `sudo` access via this entry.

!!! tip "Wrapper missing?"
    If node logs show `apt wrapper missing at /usr/local/sbin/jarvis-apt-install`, re-run `install.sh` to redeploy the wrapper.

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

Wake-word detection reads from `dsnoopmic` (raw PCM, no PA resampling); the listener resamples the 48 kHz capture to 16 kHz (openWakeWord's expected input rate) before scoring. TTS and streaming playback go through PulseAudio.

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
| openwakeword | Wake word detection (local ONNX inference; no API key or cloud service required) |
| httpx | REST client to command center |
| SQLAlchemy + pysqlcipher3 | Local encrypted database |
| jarvis-command-sdk | Shared command/agent interfaces |
| mpv | Streaming command audio playback (`--ao=alsa` path) |

HAT-specific drivers (TLV320, APA102 LEDs, gpiozero) live in `requirements-hat.txt` and are installed separately on Pi HAT nodes only.

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
| `not_for_me_quiet_seconds` | Seconds the wake gate is held after a `<not_for_me/>` response. Default: `20.0` |
| `wake_word_model` | openWakeWord model name. Default: `hey_jarvis`. Models are downloaded automatically on first run via `openwakeword.utils.download_models`. |
| `audio_output_device` | ALSA device for playback (e.g. `hw:1,0`, named PulseAudio sink). Overrides auto-detection. Container nodes: set via `JARVIS_AUDIO_OUTPUT_DEVICE` env. |

## Node Authentication

Nodes authenticate to the command center with an API key header:

```
X-API-Key: {node_id}:{api_key}
```

For development, register a node using the `authorize_node.py` utility:

```bash
python utils/authorize_node.py \
  --cc-url http://localhost:7703 \
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

## Container Deployment

The voice node ships a Docker image (`Dockerfile.audio`) for running the full voice runtime — mic capture, wake word, STT, TTS playback — on any 64-bit Linux host, with or without Pi hardware.

!!! warning "macOS is not supported via Docker"
    Docker Desktop runs containers in a VM with no access to the Mac's audio hardware. Run natively on macOS for development.

### Supported hosts

| Host | Architecture | Notes |
|------|-------------|-------|
| Raspberry Pi (64-bit OS) | arm64 | Any model; USB or HAT audio |
| Ubuntu/Debian server or desktop | amd64 | USB mic + speaker recommended |
| Any Linux with Docker | arm64 / amd64 | Requires mic + speaker accessible to the container |

### Quick start

**1. Build the image**

```bash
docker compose -f docker-compose.audio.yaml build
```

Builds for the host's native architecture — no QEMU. First build downloads onnxruntime, scipy, and the openWakeWord models; allow a few minutes.

**2. Detect audio devices and write config**

```bash
./scripts/configure-audio.sh
```

Auto-detects your host's audio transport (PipeWire/PulseAudio socket vs raw `/dev/snd`), lists available mics, writes `audio.env` (git-ignored), and prints the exact `docker compose … up` command for your system.

**3. First run — register the node**

```bash
docker compose -f docker-compose.audio.yaml up
```

On first boot there are no credentials, so the node starts the **setup web UI** on `http://<host>:7771`. Log in, pick a household and room, and point it at your command center URL. Credentials are saved to the `jarvis-node-config` Docker volume.

**4. Restart into voice mode**

```bash
docker compose -f docker-compose.audio.yaml restart
```

The node now has credentials and starts the full voice loop (wake → STT → CC → TTS playback).

### Audio transport

| Transport | Compose file(s) | When to use |
|-----------|----------------|-------------|
| Raw ALSA (`/dev/snd`) | `docker-compose.audio.yaml` | Headless server with no sound daemon; USB mic + speaker |
| PulseAudio / PipeWire socket | `docker-compose.audio.yaml` + `docker-compose.pulse.yaml` | Linux desktop — **required** there; the sound server owns the devices exclusively |

For PipeWire/PulseAudio hosts, add the overlay:

```bash
docker compose -f docker-compose.audio.yaml -f docker-compose.pulse.yaml up
# If your login UID is not 1000:
JARVIS_HOST_UID=$(id -u) docker compose -f docker-compose.audio.yaml -f docker-compose.pulse.yaml up
```

### Echo Cancellation (AEC)

AEC removes the node's own TTS playback from the mic signal so the node can hear "Hey Jarvis" over its own audio (barge-in). Requires the PulseAudio/PipeWire transport. Enable with:

```bash
JARVIS_AEC_ENABLED=true   # in audio.env
```

Validated in-container on Ubuntu/PipeWire: calibration succeeds, the pipeline runs per-frame with no errors. Most useful with open speakers; a closed headset has minimal echo.

### Container environment variables

| Variable | Meaning | Default |
|----------|---------|---------|
| `JARVIS_AUDIO_OUTPUT_DEVICE` | ALSA playback device (e.g. `plughw:1,0`, named sink, `pulse`) | `default` |
| `JARVIS_MIC_DEVICE_INDEX` | PyAudio input index | auto (first input) |
| `JARVIS_MIC_DEVICE_NAME` | Substring match against input device name (more stable than index across reboots) | — |
| `JARVIS_MIC_SAMPLE_RATE` | Mic capture rate; runtime resamples to 16 kHz internally. Try `44100` for USB mics that reject 48 kHz | `48000` |
| `JARVIS_HOST_UID` | Host login UID used for the PipeWire socket path | `1000` |
| `JARVIS_AEC_ENABLED` | Enable acoustic echo cancellation (requires pulse transport) | `false` |

### Container troubleshooting

- **No input devices / `PyAudio.open()` fails** — confirm `/dev/snd` exists on the host and `arecord -l` shows the mic. The compose file adds the container user to the `audio` group automatically.
- **Playback silent** — set `JARVIS_AUDIO_OUTPUT_DEVICE` to a specific device from `aplay -L` on the host. `default` may map to the wrong card on multi-device systems.
- **Wake word never fires** — run `docker compose -f docker-compose.audio.yaml exec jarvis-node-audio python scripts/list_audio_devices.py` to verify the mic is visible. Lower `JARVIS_MIC_SAMPLE_RATE` if the device doesn't support 48 kHz.
- **Can't reach the command center** — the container maps `host.docker.internal` to the host IP. Use that hostname in the setup UI when CC runs on the same machine.

### Docker images (CI-published)

| Tag | Trigger | Architectures |
|-----|---------|--------------|
| `:edge` | Every merge to `main` | amd64, arm64 |
| `:latest` | `v*` git tag | amd64, arm64 |
| `:<version>` | `v*` git tag | amd64, arm64 |

Images are built with native per-arch runners (no QEMU), so arm64 builds take ~3 minutes instead of ~38.

## Service Dependencies

| Service | Required | Purpose |
|---------|----------|---------|
| Command Center (7703) | Yes | Voice command processing |
| TTS (7707) | No | Spoken responses via MQTT |
| Config Service (7700) | No | Service discovery |
