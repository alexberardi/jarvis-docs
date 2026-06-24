# Nodes

The Nodes tab manages your Pi Zero voice nodes --- the physical devices that capture voice commands.

## Node List

Each node card shows:

- Room name
- Node ID
- Operating mode (brief/full)

Tap a node to view its detail screen with settings, installed commands, and status.

## Adding a Node

Tap **Add Node** to start the provisioning flow:

1. **Scan** --- The app scans for nearby Jarvis nodes broadcasting a WiFi access point
2. **Connect** --- Connect to the node's AP network
3. **Configure** --- Enter your home WiFi credentials
4. **Register** --- The node registers with the command center

!!! tip
    For development, you can use **Import Key** (top right) to manually pair a node by pasting its K2 encryption key.

## Node Settings

From a node's detail screen you can:

- View installed commands and their settings
- Configure command secrets (API keys, credentials)
- Trigger device discovery
- View node status and connection info

## Voice Settings

Each node exposes a **Voice Settings** screen where you can tune wake-word detection, audio I/O, and response behaviour.

| Setting | Default | Description |
|---|---|---|
| **Wake Word Model** | `hey_jarvis` | openWakeWord model name. Change for a custom or non-English wake word. |
| **Not-For-Me Quiet Time** | 20 s (range 5–60 s) | How long to suppress further wakes after one is classified as not meant for this node (ambient false-wake suppression). |
| **Audio Output Device** | *(auto-detect)* | ALSA playback device string for TTS output (e.g. `plughw:1,0`). Leave blank to let the node auto-detect. |
| **Mic Sample Rate** | 48000 Hz | Microphone capture rate. Constrained to 44100 or 48000 Hz. Use 44100 only for USB mics that reject the higher rate; audio is resampled to 16 kHz for the wake-word detector either way. |

Tap **Save Changes** to persist settings to the node. Changes take effect on the next voice-session start.
