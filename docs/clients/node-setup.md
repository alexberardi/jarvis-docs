# Node (jarvis-node-setup)

The Jarvis node is the primary voice interface for Jarvis. It runs on Raspberry Pi hardware (Pi Zero 2 W, Pi 4, Pi 5), any 64-bit Linux machine, or inside Docker with a mic and speaker attached. macOS is supported for development (native only; Docker Desktop has no audio hardware access via VM).

This Python node is the **supported** Pi voice node. It talks to `jarvisd`, the Jarvis Automation server, at one address: `http://<server>:7700`. Install the server first (see [Install](../install/index.md)); Jarvis Automation is a **pre-release** (release candidate rc18).

This page starts with installing and running a node, then its settings and troubleshooting. The node's internals, for people working on `jarvis-node-setup` or writing commands, are at the end under [For developers](#for-developers).

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-node-setup/v0.3.6/install.sh | sudo bash
```

This installs to `/opt/jarvis-node`, sets up a systemd service, and configures audio. A fresh node then opens its setup hotspot; pair it with your server from the mobile app (**Add Node**, see [Provisioning](provisioning.md)). The app gives the node your server's address, the same `http://<server>:7700` the app itself uses, and the node finds everything else from it.

A node that was paired with the old Docker install keeps its key when you move to `jarvisd` with `jarvisd import-legacy`, and reconnects without being set up again; see [Migrating from the old install](../install/migrating-from-docker.md).

Flags:

| Flag | Description |
|------|-------------|
| `--no-audio` | Skip ALSA / I2S DAC configuration |
| `--force` | Reinstall even if already at latest version |
| `--version TAG` | Install a specific version (e.g. `v0.3.6`) |
| `--local` | Skip the download and install from a tarball already staged in `/opt/jarvis-node` |

The installer runs the node as the `pi` user, with the `XDG_RUNTIME_DIR` that PulseAudio needs, and stages the default `hey_jarvis` wake-word model (unless `--no-audio`). It needs internet access for that download; see [Troubleshooting](#troubleshooting) if wake word never fires.

## Go Pi node (experimental preview)

!!! warning "Experimental: keep the Python node"
    Each `jarvis-server` release also carries `install-pi.sh`, which installs the **Go** voice node (`jarvis-agent --profile pi`). It is an experimental preview, not a replacement yet: the Python node above stays the supported Pi node until the Go node passes its 24-hour soak and closes the gaps below. Try it on a spare Pi, not the one your household relies on.

What it needs and what it is:

- A Raspberry Pi with the **ReSpeaker 2-Mics HAT v2.0**, running **64-bit** Raspberry Pi OS (the script refuses anything but arm64).
- It installs next to the Python node, **disabled**. Only one node can own the HAT; `--activate` stops the Python node and makes the Go node the one that runs at boot, and `--deactivate` switches back. Nothing is removed either way.
- It enrolls as a **new** node: it does not take over the Python node's id, room or settings.
- It needs far less memory than the Python node: an estimated ~160 MB with its command sidecar and PulseAudio on a Pi Zero 2 W, against 340–420 MB. That is why it is being built.

Known gaps in this preview:

- Wake words over music fail more often (no echo cancellation yet), and there is no wake-word auto-calibration or false-wake cool-down. A Pi without the HAT has no LEDs.
- "Turn on the kitchen light", routines and "send me a link" do not work **by voice** on the Go node yet; device control from the app does.
- The app's node settings may not reach a Go node yet (not confirmed).
- A bad release that keeps crashing may not roll back on its own.
- A factory reset that brings the node back into setup mode is built but not yet checked on a Pi.

Install it from the release (pin the tag; every release so far is a pre-release, so there is no "latest" download link):

```bash
curl -fsSLo install-pi.sh https://github.com/alexberardi/jarvis-server/releases/download/v0.1.0-rc18/install-pi.sh
sudo sh install-pi.sh                     # installs the Go node, disabled
/opt/jarvis-agent/jarvis-agent enroll --server <server> --room <room>
sudo sh install-pi.sh --activate          # make it the node that runs (--deactivate goes back)
```

Run `enroll` as the node's user (`pi` by default). It prints a code: approve it in the mobile app or on the web app's **Nodes** page. The script checks the download against the release's `SHA256SUMS` (and `SHA256SUMS.minisig` when `minisign` is installed). A change to `config.txt` or the HAT overlay takes effect after a reboot.

## What It Does

1. **Wake word detection** -- Listens locally for a configured wake word using [openWakeWord](https://github.com/dscripka/openWakeWord). Local ONNX inference — no cloud service or API key required. The model is set via `wake_word_model` in `config.json` (default: `hey_jarvis`). No audio leaves the device until the wake word is heard.
2. **Audio capture** -- Records speech until silence is detected.
3. **Command submission** -- Sends the audio to the server, which transcribes it, works out what you asked for and runs the command.
4. **Response playback** -- Receives the spoken response from the server over MQTT and plays it through the speaker.

### Volume and mute by voice

The built-in `control_node` command handles volume and mute on the node itself, without a round trip to the model.

| Action | Trigger phrases | Notes |
|--------|----------------|-------|
| Volume up | "volume up", "louder", "crank it up", "turn it up" | +10 percentage points |
| Volume down | "volume down", "quieter", "softer", "turn it down" | −10 percentage points |
| Set volume | "set volume to 50", "volume 7", "volume 75%" | N ≤ 10 maps to N×10%; N > 10 is literal % |
| Mute | "mute", "mute the speaker", "please mute" | |
| Unmute | "unmute", "unmute the volume" | |

Volume is saved to `config.json` as `volume_percent` and restored on restart. Changes apply to the default speaker and any paired Bluetooth speakers together.

The built-in time command also answers date questions from the node's clock: "what day is it" (and "tomorrow" / "yesterday"), "what's the date", "what year is it", "what month is it", "is it the weekend" and "how many days until Christmas".

### ReSpeaker 2-Mics HAT v2

The node has first-class support for the [Seeed Studio ReSpeaker 2-Mics Pi HAT v2](https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT/). When the HAT is present, the mobile app shows its controls (LED brightness, button):

- **LEDs**: `led_enabled` and `led_brightness_percent` in `config.json` are applied at startup, so the LEDs don't flash at full brightness on boot.
- **Button**: a short press speaks any queued alerts and clears them, or says "No new notifications." A long press (hold) shuts the node down.

## Running in Docker

The voice node also runs in a container (`Dockerfile.audio`): mic capture, wake word and playback on any 64-bit Linux host, with or without Pi hardware.

!!! warning "macOS is not supported via Docker"
    Docker Desktop runs containers in a VM with no access to the Mac's audio hardware. Run natively on macOS for development.

### Supported hosts

| Host | Architecture | Notes |
|------|-------------|-------|
| Raspberry Pi 4 or 5 (64-bit OS) | arm64 | USB or HAT audio. A Pi Zero 2 W should use the native install above |
| Ubuntu/Debian server or desktop | amd64 | USB mic + speaker recommended |
| Any Linux with Docker | arm64 / amd64 | Requires mic + speaker accessible to the container |

### Images

Each release publishes two images to GitHub's container registry, for amd64 and arm64:

| Image | What it is |
|-------|-----------|
| `ghcr.io/alexberardi/jarvis-node-audio` | The voice node with host audio (this section) |
| `ghcr.io/alexberardi/jarvis-node` | The node without audio (`docker-compose.yaml`) |

| Tag | Trigger |
|-----|---------|
| `:edge` | Every merge to `main` |
| `:latest` | `v*` git tag |
| `:<version>` | `v*` git tag |

### Quick start

The steps use a checkout of `jarvis-node-setup`.

**1. Get the image**

The repo's `docker-compose.audio.yaml` builds the image locally, which needs the `jarvis-command-sdk` repo checked out next to it (`../jarvis-command-sdk`). To use the published image instead, replace the service's `build:` block with:

```yaml
    image: ghcr.io/alexberardi/jarvis-node-audio:<version>
```

**2. Detect audio devices and write config**

```bash
./scripts/configure-audio.sh
```

Auto-detects your host's audio transport (PipeWire/PulseAudio socket vs raw `/dev/snd`), lists available mics, writes `audio.env` (git-ignored), and prints the exact `docker compose … up` command for your system.

**3. First run — register the node**

```bash
docker compose -f docker-compose.audio.yaml up
```

On first boot there are no credentials, so the node starts the **setup web UI** on `http://<host>:7771`. Log in, pick a household and room, and point it at your server, `http://<server>:7700`. Credentials are saved to the `jarvis-node-config` Docker volume.

**4. Restart into voice mode**

```bash
docker compose -f docker-compose.audio.yaml restart
```

The node now has credentials and starts the full voice loop (wake word → server → spoken reply).

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

AEC removes the node's own playback from the mic signal so the node can hear "Hey Jarvis" over its own audio (barge-in). Requires the PulseAudio/PipeWire transport. Enable with:

```bash
JARVIS_AEC_ENABLED=true   # in audio.env
```

Most useful with open speakers; a closed headset has minimal echo.

### Container environment variables

| Variable | Meaning | Default |
|----------|---------|---------|
| `JARVIS_AUDIO_OUTPUT_DEVICE` | ALSA playback device (e.g. `plughw:1,0`, named sink, `pulse`) | `default` |
| `JARVIS_MIC_DEVICE_INDEX` | PyAudio input index | auto (first input) |
| `JARVIS_MIC_DEVICE_NAME` | Substring match against input device name (more stable than index across reboots) | — |
| `JARVIS_MIC_SAMPLE_RATE` | Mic capture rate; runtime resamples to 16 kHz internally. Try `44100` for USB mics that reject 48 kHz | `48000` |
| `JARVIS_HOST_UID` | Host login UID used for the PipeWire socket path | `1000` |
| `JARVIS_AEC_ENABLED` | Enable acoustic echo cancellation (requires pulse transport) | `false` |
| `JARVIS_CONFIG_URL_STYLE` | Overrides how the node rewrites service addresses (`external`/`dockerized`). Leave it unset: the node works it out itself. | *(auto-computed)* |

## Configuration

A provisioned node keeps its settings in `/opt/jarvis-node/config.json`. Provisioning writes the first ones; most of the rest are changed from the mobile app's node settings. Development nodes use `config-mac.json` (git-ignored).

| Field | Description |
|-------|-------------|
| `node_id` | The node's id, assigned during registration |
| `api_key` | API key the node authenticates to the server with |
| `jarvis_config_service_url` | The server's address, `http://<server>:7700`. The only address the node reads from the file: it finds every service from it |
| `jarvis_command_center_api_url` | The command address provisioning was given (`http://<server>:7700/cc` on `jarvisd`). The node will not start without it, but resolves the address it uses from `jarvis_config_service_url` |
| `room` | Room name (e.g., "kitchen", "office") |
| `household_id` | Household UUID for multi-tenant isolation |
| `release_track` | Update channel: `"stable"` (default) or `"dev"`. Set from the mobile app (see [Update Policy](#update-policy)). |
| `allow_updates` | Consent gate for update tasks — a node refuses (and reports) updates unless `true`. Set from the mobile app; see [Update Policy](#update-policy). |
| `wake_word_model_autodownload_enabled` | Whether openWakeWord model files auto-download at boot. Defaults off; a fresh install still gets a model from `install.sh`. Set from the mobile app; see [Update Policy](#update-policy). |
| `volume_percent` | Persisted speaker volume (0–100); written on every volume command |
| `led_enabled` | Whether the LED ring is active on boot (HAT nodes only) |
| `led_brightness_percent` | LED brightness applied at startup (0–100, default 100) |
| `wake_word_model` | openWakeWord model name. Default: `hey_jarvis`. Staged by `install.sh` on fresh installs and restored across updates; runtime autodownload only applies if `wake_word_model_autodownload_enabled` is set. |
| `wake_debounce_secs` | See [Wake Behavior](#wake-behavior). Default: `8.0` |
| `not_for_me_quiet_seconds` and related keys | See [Wake Behavior](#wake-behavior). Default: `20.0` |
| `listen_onset_wait_secs` | See [Wake Behavior](#wake-behavior). Default: `0` (off) |
| `audio_output_device` | ALSA device for playback (e.g. `hw:1,0`, named PulseAudio sink). Overrides auto-detection. Container nodes: set via `JARVIS_AUDIO_OUTPUT_DEVICE` env. |

### Wake Behavior

The node holds one gate that decides when the next wake word is accepted (`core/voice_filters.py`, checked in `core/wake_detector.py`). Two things push it forward:

| Source | Default | Trigger |
|--------|---------|---------|
| Same-utterance debounce | 8 s | Every accepted wake — stops openWakeWord from scoring the same "Hey Jarvis" on consecutive 80 ms chunks |
| `not_for_me` cool-down | 20 s, 60 s when repeated | The server answered `<not_for_me/>` (you were talking to someone else); side conversations cluster, so the cool-down stops the re-trigger loop |

A later or longer deadline wins; they do not stack.

#### The not_for_me cool-down

The cool-down is soft: a wake word spoken clearly enough (a score of at least `not_for_me_override_threshold`) gets through at once, so a real question after a misclassified one is not locked out. Ambient speech that barely reaches the base threshold stays suppressed.

| Key | Default | Meaning |
|-----|---------|---------|
| `not_for_me_quiet_seconds` | `20.0` | Cool-down after one `<not_for_me/>`. `0` or less turns the cool-down off |
| `not_for_me_escalated_quiet_seconds` | `60.0` | Cool-down once there have been 2 or more within the window |
| `not_for_me_escalation_window_seconds` | `120.0` | The window for counting repeats |
| `not_for_me_override_threshold` | `0.6` | Wake score that gets through an armed cool-down |

Raise the quiet seconds if side conversations keep looping; lower them, or lower the override threshold, if real follow-ups are dropped.

```json
{
  "not_for_me_quiet_seconds": 20.0
}
```

#### The debounce

Set `wake_debounce_secs` in `config.json` (default `8.0`) to change how long an accepted wake blocks the next one. The
default also swallows a repeat request made within a few seconds of an answer; lower it if your household talks back
quickly. Values below `0.5` are raised to `0.5` so one "Hey Jarvis" cannot fire twice on consecutive chunks.

```json
{
  "wake_debounce_secs": 3.0
}
```

#### Pauses after the wake word

By default the recording stops as soon as the end-of-speech silence window passes, counted from the first chunk, so
someone who says "Hey Jarvis" and then pauses is stopped before they start. Set `listen_onset_wait_secs` (default `0`,
off) to hold the silence stop until speech has been heard, for up to that many seconds:

```json
{
  "listen_onset_wait_secs": 2.0
}
```

If no speech arrives within the wait, the recording ends as it would have anyway.

### Update Policy

A node applies an update only when its `allow_updates` consent flag is on. When it refuses one, it tells the server why, so the app shows the reason instead of a timeout.

`allow_updates`, `wake_word_model_autodownload_enabled` and `release_track` are set from the mobile app's node screen (see [Software Updates](../mobile/nodes.md#software-updates)). They travel end-to-end encrypted with the node's K2 key, so the server cannot change them, and the node refuses a replayed older change. Nodes too old to have the gate show no consent controls.

!!! note "Fielded nodes need one manual opt-in"
    Nodes on 0.1.130–0.1.136 have the underlying gate but predate the app's controls — they need one SSH opt-in (or a direct `config.json` edit) before they can be updated to a newer version.

### Keeping voice on the LAN

When the server hands out **public** addresses (`jarvisd` does once a service has a public URL on the web app's **Connections** page), a node in the same house would send its audio out to the internet and back, about 2 s per turn. Point it at the server's LAN address instead, in the node's `.env`:

```bash
JARVIS_COMMAND_CENTER_LAN_URL=http://<server-lan-ip>:7700/cc
```

That keeps voice on the local network (a few milliseconds). The override is per node and per service (`JARVIS_<SERVICE>_LAN_URL`); remote nodes leave it unset. Only the command service matters for voice, because the node reaches speech-to-text and text-to-speech through it. `JARVIS_CONFIG_URL` can likewise point the node's first lookup at the server's LAN address.

## Troubleshooting

### The node can't reach the server

Everything is on the one `jarvisd` server. The node needs only its address; the rest resolves through it.

| What | Required | Purpose |
|---------|----------|---------|
| The server address, port 7700 | Yes (once provisioned) | Every other service address is looked up there. Only tolerated as unreachable while a node is still provisioning. |
| Commands, found from 7700 | Yes | Voice command processing; the node reaches speech-to-text and text-to-speech through it |
| MQTT broker, found from 7700 | Yes | Spoken responses and server→node messages |

Run `jarvisd doctor` on the server: it checks what nodes and phones need to reach. A node that cannot reach the server keeps retrying and recovers by itself when the server is back.

In Docker on the same machine as `jarvisd`, use `http://host.docker.internal:7700` as the server address in the setup UI; the container maps that name to the host.

### Wake word never fires

- On a fresh install, `install.sh` downloads the `hey_jarvis` model. An offline install skips it with a warning, and the node runs without wake word. Re-run the installer with internet access, or turn on `wake_word_model_autodownload_enabled` from the app.
- After an update, the installer copies the models from the previous install. If it warns that it could not, do the same.
- In a container, run `docker compose -f docker-compose.audio.yaml exec jarvis-node-audio python scripts/list_audio_devices.py` to check the mic is visible, and lower `JARVIS_MIC_SAMPLE_RATE` if the device doesn't support 48 kHz.

Log lines to watch with `journalctl -u jarvis-node`:

| Log key | Meaning |
|---------|---------|
| `wake-suppressed-gate` | A wake score above 0.3 was suppressed by the gate; includes `cooldown_remaining_sec` |
| `wake-override-cooldown` | A clear wake word got through an armed `not_for_me` cool-down |
| `not-for-me-cooldown-armed` | The server answered `<not_for_me/>`; includes `cooldown_sec` |

### No sound, or audio fails silently

- PulseAudio needs `XDG_RUNTIME_DIR`. The installer's unit sets it (with `User=pi`); a unit you wrote by hand needs `Environment=XDG_RUNTIME_DIR=/run/user/<uid of the user>` and must not run as root.
- In a container, set `JARVIS_AUDIO_OUTPUT_DEVICE` to a device from `aplay -L` on the host; `default` may map to the wrong card on multi-device systems. If `PyAudio.open()` fails, check `/dev/snd` exists on the host and `arecord -l` shows the mic.

### A Pantry install fails with "apt wrapper missing"

If node logs show `apt wrapper missing at /usr/local/sbin/jarvis-apt-install`, re-run `install.sh` to put the wrapper back.

## For developers

This part is for working on `jarvis-node-setup` itself or writing commands for it.

### Architecture

```
jarvis-node-setup/
├── scripts/
│   ├── main.py                # Native entry point
│   ├── entrypoint.py          # Container entry point (routes setup / voice mode)
│   ├── voice_listener.py      # The voice loop
│   ├── mqtt_tts_listener.py   # MQTT listener for spoken replies
│   ├── command_store.py       # Command store CLI (install, remove, list, update)
│   ├── jarvis-apt-install     # Sudo-able apt-get shim for Pantry-declared packages
│   └── configure-audio.sh     # Audio device auto-detect for containerised runs
├── core/
│   ├── voice_filters.py       # Wake gate and not_for_me cool-down
│   ├── wake_detector.py       # Wake-word scoring against the gate
│   ├── ijarvis_parameter.py   # Parameter definitions
│   ├── ijarvis_secret.py      # Secret definitions
│   ├── command_response.py    # Response structure
│   └── platform_abstraction.py # Hardware abstraction (Pi vs generic Linux)
├── commands/                  # Built-in commands (control_node, timers, ...)
├── agents/                    # Background agents (reminders, device discovery)
├── services/
│   ├── secret_service.py      # Encrypted secret management
│   ├── agent_scheduler_service.py  # Background agent scheduling
│   ├── alert_queue_service.py # Proactive alert queue + button announce
│   ├── button_service.py      # ReSpeaker GPIO17 button handler
│   ├── settings_snapshot_service.py # Settings snapshot builder
│   └── reminder_service.py    # Persistent reminders
├── stt_providers/
│   └── jarvis_whisper_client.py  # Speech-to-text client (through the server)
├── provisioning/              # Headless provisioning system
└── utils/
    ├── audio_volume.py        # PulseAudio volume/mute control
    ├── authorize_node.py      # Register a node without the app
    ├── config_service.py      # Configuration loader
    ├── config_env.py          # JARVIS_CONFIG_URL_STYLE selection, shared by main.py and entrypoint.py
    └── service_discovery.py   # Service URL resolution from the server address
```

Commands import `IJarvisCommand` straight from the SDK (`from jarvis_command_sdk import IJarvisCommand`).

### Platform detection

`core/platform_abstraction.py` exposes two probes used at runtime:

- `is_raspberry_pi()` — reads the device-tree model string; returns `True` only on Pi hardware.
- `has_respeaker_hat()` — checks for the `seeed2micvoicec` ALSA card; gates TLV320 self-heal and sink keepalive.

On non-Pi 64-bit Linux (and in containers), `LinuxHostAudioProvider` is selected instead of the HAT-specific provider. HAT-specific drivers ship in `requirements-hat.txt` and are not installed by default.

### Threading model

The node runs multiple supervised threads:

- **Main thread** -- Voice listener. Detects wake word, captures audio, sends it to the server.
- **MQTT thread** -- Receives spoken replies from the broker and plays them through the speaker.
- **Agent scheduler** -- Runs background agents on configurable intervals (reminders, device discovery, token refresh).
- **ButtonShortPress thread** -- Handles ReSpeaker GPIO17 short-press events. Speaks queued alerts via local TTS without blocking the GPIO callback. Started after TTS, LED, and alert-queue services are ready.

### Service discovery

The node reads one address from `config.json`, `jarvis_config_service_url` (the server's port 7700), and resolves every service it needs from there through `utils/service_discovery.py`: commands (`/cc`), the MQTT broker, speech-to-text, text-to-speech and sign-in. There is no fallback to other `config.json` keys or to `localhost`:

- **Fail loud.** A provisioned node that can't resolve a service raises `ServiceUnresolvedError` instead of making up an address.
- **Provisioning is the one exception.** A node without a `.provisioned` marker (or with `JARVIS_SKIP_PROVISIONING_CHECK` set) isn't expected to reach the server yet, so unresolved services return `""` there instead of raising.
- **Callers retry, they don't degrade.** The voice listener retries an unreachable server indefinitely with capped backoff and recovers when it returns; audio failures get a bounded retry, then the node runs headless. The MQTT loop re-resolves the broker on every retry (backoff up to 60 s).

The node also works out from the server address whether the addresses it gets back need rewriting (`utils/config_env.py`, `JARVIS_CONFIG_URL_STYLE`): `external` for a real IP or hostname, `dockerized` for `host.docker.internal`, none for `localhost`. Leave the variable unset; it is recomputed on every start. `JARVIS_<SERVICE>_LAN_URL` short-circuits the lookup for one service (see [Keeping voice on the LAN](#keeping-voice-on-the-lan)).

### Writing commands

Commands live in the `commands/` directory, or come from the Pantry. Each one implements `IJarvisCommand` from the [command SDK](../libraries/command-sdk.md), which lists the abstract members: `command_name`, `description`, `generate_prompt_examples()`, `generate_adapter_examples()`, `parameters`, `required_secrets`, `keywords` and `run(self, request_info, **kwargs)`. The server builds the model's tool definitions from these; when the model picks a command, the node calls the SDK's `execute()`, which validates the arguments and calls `run()`. See the [Interface Reference](../commands/interface-reference.md) for the rest.

#### Pre-routing (fast path)

Commands can implement `pre_route()` to claim short, unambiguous utterances without LLM inference:

```python
def pre_route(self, voice_command: str) -> PreRouteResult | None:
    if voice_command.strip().lower() == "pause":
        return PreRouteResult(arguments={}, spoken_response="Paused.")
    return None
```

This skips the LLM entirely, reducing latency to near-zero for simple commands like "pause" or "stop". `control_node` and the time command's date answers work this way.

### Installing commands from the Pantry

Install commands from the mobile app's [Pantry](../mobile/pantry.md) tab, or on the node with the command store CLI:

```bash
python scripts/command_store.py install get_weather
python scripts/command_store.py install --url <github_url> [--version <tag>]
python scripts/command_store.py list
```

The install pipeline runs these steps in order: clone → validate → test → copy files → **apt deps** → pip deps → namespace → secrets → registry enable. apt runs before pip so a fast failure (disk full, bad package name, missing wrapper) aborts before the slower pip work begins.

#### apt dependencies

Commands that declare system packages in their manifest (`apt_packages` field) trigger an apt install step. The installer:

1. **Pre-flights disk space** — requires ≥ 500 MB free on `/`. Fails fast before invoking apt if the check fails.
2. **Validates package names** — each name is checked against `^[a-z][a-z0-9.+-]*$`. One invalid name aborts the entire call with no partial installs.
3. **Invokes `/usr/local/sbin/jarvis-apt-install`** via `sudo` — a root-owned POSIX sh wrapper deployed by `install.sh` that forwards valid names to `nice -n 15 apt-get install -y --no-install-recommends` with a 60 s dpkg-lock wait and a 300 s total timeout.

The installer adds this entry to `/etc/sudoers.d/jarvis-node`:

```
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/local/sbin/jarvis-apt-install *
```

The `*` is in the argument position (not the binary path), so only `jarvis-apt-install` itself can be invoked with elevated privileges — no other command gains `sudo` access via this entry.

### Audio internals

The node uses **PulseAudio** for playback and mute control. The wake-word capture path uses ALSA `dsnoop` directly to avoid PulseAudio resampling and AGC latency. Runtime volume and mute go through `pactl` (`set-sink-volume`, `set-sink-mute`), on the default sink and every `bluez_sink.*` Bluetooth sink together.

The installer writes an asymmetric `/etc/asound.conf` that routes playback through PulseAudio while keeping capture on the raw hardware device:

```
pcm.output         type pulse          — playback via PulseAudio
pcm.dsnoopmic_hw   type dsnoop         — shared capture on hw:seeed2micvoicec,0
                                          ipc_key 87654321, 2ch, 48000 Hz, S16_LE
pcm.dsnoopmic      type plug → dsnoopmic_hw
pcm.!default       type asym: playback=output, capture=dsnoopmic
```

Wake-word detection reads from `dsnoopmic` (raw PCM, no PA resampling); the listener resamples the 48 kHz capture to 16 kHz (openWakeWord's expected input rate) before scoring.

The `hardware` block in every settings snapshot tells the app which HAT controls to show:

| Field | Type | Description |
|-------|------|-------------|
| `hat_detected` | bool | `true` when ReSpeaker HAT is present |
| `led_chain_available` | bool | `true` when the APA102 LED ring is available (equals `hat_detected`) |
| `audio_card` | string \| null | ALSA card name, e.g. `"seeed2micvoicec"`; `null` on macOS or no HAT |
| `is_muted` | bool | Current PulseAudio mute state; omitted if indeterminate |
| `button_available` | bool | `true` when gpiozero is importable and `hat_detected` is `true` |

### Wake-word models across updates

The openWakeWord models live inside the venv (`site-packages/openwakeword/resources/models/`), which every update replaces. `install.sh` therefore runs `restore_wake_models()` (copy `*.onnx` / `*.tflite` forward from the `${INSTALL_DIR}.bak` venv, never overwriting models the node staged itself) and then `stage_default_wake_model()` (download `hey_jarvis` if no `.onnx` is staged; skipped with `--no-audio`). Both are best-effort: a failure warns and the install carries on.

### Update policy internals

The three policy keys are written only through the `node_config` config push: a strict allowlist (`allow_updates`, `wake_word_model_autodownload_enabled`, `release_track` ∈ `stable`/`dev`), real booleans only (a string `"false"` is rejected), and an `__issued_at` timestamp checked against a stored watermark so a stale payload is refused. The older plaintext `update_node_config` channel rejects these keys (and any `_`-prefixed key). A refused update is reported with `POST /api/v0/nodes/tasks/{id}/status`. All `config.json` writers go through one locked, atomic write.

### Local encrypted storage

Node secrets (API keys, OAuth tokens) are stored in a local SQLite database encrypted with [PySQLCipher](https://github.com/niccokunzmann/pysqlcipher3). The encryption key (`K1`) is generated on first boot and stored in `~/.jarvis/secrets.key`, so secrets are encrypted at rest on the SD card.

### Dependencies

| Library | Purpose |
|---------|---------|
| PyAudio, SoundDevice | Audio capture and playback |
| paho-mqtt | MQTT integration (spoken replies) |
| openwakeword | Wake word detection (local ONNX inference; no API key or cloud service required) |
| httpx | REST client to the server |
| SQLAlchemy + pysqlcipher3 | Local encrypted database |
| jarvis-command-sdk | Shared command/agent interfaces |
| mpv | Streaming command audio playback (`--ao=alsa` path) |

HAT-specific drivers (TLV320, APA102 LEDs, gpiozero) live in `requirements-hat.txt` and are installed separately on Pi HAT nodes only.

### Node authentication

Nodes authenticate to the server with an API key header:

```
X-API-Key: {node_id}:{api_key}
```

The usual way to get one is the mobile app's **Add Node** flow, or the web app's **Nodes** page. To register a development node without either, use `utils/authorize_node.py`:

```bash
python utils/authorize_node.py \
  --cc-url http://<server>:7700/cc \
  --cc-key "$ADMIN_API_KEY" \
  --household-id <household-uuid> \
  --room office --name dev-mac \
  --update-config config-mac.json
```

The script uses the admin node routes, which `jarvisd` refuses unless it was started with the `ADMIN_API_KEY` environment variable set; pass the same value as `--cc-key`.
