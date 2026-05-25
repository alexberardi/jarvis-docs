# Device Control

Jarvis uses a two-tier architecture for smart home device control:

1. **Device Managers** / The Stewards (`IJarvisDeviceManager`) --- high-level backends that maintain the master device inventory. A steward might consult Home Assistant (an external authority) or aggregate several translators directly.
2. **Device Protocols** / The Translators (`IJarvisDeviceProtocol`) --- low-level protocol adapters that speak each device family's native language over LAN or cloud APIs (LIFX bulbs, Kasa switches, Govee lights, Apple TV).

The `control_device` command does not care which tier handles a device. It asks the active device manager for a device list, matches the user's intent, and delegates control.

## Architecture

```mermaid
graph TD
    CMD["control_device command"] --> DM["Active Device Manager"]
    DM --> HA["HA Device Manager<br/>(Home Assistant WebSocket)"]
    DM --> JD["Jarvis Direct Manager"]
    JD --> LIFX["LIFX Protocol<br/>(UDP 56700)"]
    JD --> Kasa["Kasa Protocol<br/>(python-kasa)"]
    JD --> Govee["Govee Protocol<br/>(REST + LAN)"]
    JD --> Apple["Apple Protocol<br/>(mDNS/pyatv)"]
```

## Managers vs Protocols

| Aspect | Device Manager | Device Protocol |
|--------|---------------|----------------|
| Interface | `IJarvisDeviceManager` | `IJarvisDeviceProtocol` |
| Package | `device_managers/` | `device_families/` |
| Scope | Aggregates many devices (possibly many protocols) | Controls one protocol/device family |
| Discovery | `DeviceManagerDiscoveryService` | `DeviceFamilyDiscoveryService` |
| Example | Home Assistant (hundreds of entities), Jarvis Direct (aggregates all protocols) | LIFX (UDP LAN bulbs), Kasa (TP-Link switches) |

**When to write a Device Manager:** You have a platform that already aggregates devices (like Home Assistant, SmartThings, or a proprietary hub) and you want Jarvis to pull its device list.

**When to write a Device Protocol:** You want to control a specific device family directly over LAN or cloud API, without an intermediary platform.

## The Normalized Device Format

Both tiers produce a common `DeviceManagerDevice` dataclass so the rest of the system does not need to know where a device came from:

```python
@dataclass
class DeviceManagerDevice:
    name: str               # Human-readable name ("Living Room Light")
    domain: str             # HA-style domain ("light", "switch", "climate", "media_player")
    entity_id: str          # Unique ID ("light.living_room")
    is_controllable: bool   # Can Jarvis send commands to this device?
    manufacturer: str       # "LIFX", "TP-Link", "Govee"
    model: str              # "A19", "KP125", "H6061"
    protocol: str           # "lifx", "kasa", "govee", "homeassistant"
    local_ip: str | None    # LAN IP if available
    mac_address: str | None # MAC address if available
    cloud_id: str | None    # Cloud/vendor device ID
    area: str | None        # Room or area ("living_room", "kitchen")
    state: str | None       # Current state ("on", "off", "72F")
    extra: dict | None      # Protocol-specific metadata
```

This format is used for:

- Device list display in the mobile app
- Command matching (the LLM sees device names and domains)
- Settings sync snapshots (`get_all_managers_for_snapshot()`)

## Available Device Packages

The following device integrations are available as Pantry packages. Install via `jarvis pantry install <package-name>`.

### Lighting

| Package | Devices | Connection | Setup Required |
|---------|---------|------------|----------------|
| `jarvis-device-lifx` | LIFX bulbs, strips, beams | LAN (UDP 56700) | None — pure broadcast discovery |
| `jarvis-device-govee` | Govee lights, strips, plugs | Hybrid (LAN + cloud) | `GOVEE_API_KEY` from developer.govee.com |
| `jarvis-device-kasa` | TP-Link Kasa/Tapo switches, bulbs, dimmers | LAN broadcast | None — auto-discovery |
| `jarvis-device-hue` | Philips Hue lights | LAN (Hue Bridge) | Bridge IP + API username (press link button once) |

### Climate & Security

| Package | Devices | Connection | Setup Required |
|---------|---------|------------|----------------|
| `jarvis-device-resideo` | Honeywell Home / Resideo thermostats | Cloud (Home API v2) | `RESIDEO_CONSUMER_KEY`, `RESIDEO_CONSUMER_SECRET` + OAuth |
| `jarvis-device-nest` | Google Nest thermostats, cameras | Cloud (SDM API) | Device Access registration ($5 one-time) + `NEST_PROJECT_ID` + OAuth |
| `jarvis-device-simplisafe` | SimpliSafe security systems | Cloud (unofficial API) | SimpliSafe account + MFA enabled + browser-based OAuth (PKCE) |

### Locks & Access

| Package | Devices | Connection | Setup Required |
|---------|---------|------------|----------------|
| `jarvis-device-schlage` | Schlage Encode WiFi smart locks | Cloud (pyschlage) | Schlage account email + password |

### Appliances

| Package | Devices | Connection | Setup Required |
|---------|---------|------------|----------------|
| `jarvis-device-homeconnect` | Bosch/Siemens dishwashers and appliances | Cloud (Home Connect API) | Home Connect developer account + Client ID/Secret + OAuth |

### Media & Smart Home

| Package | Devices | Connection | Setup Required |
|---------|---------|------------|----------------|
| `jarvis-device-apple` | Apple TV, HomePod | LAN (mDNS/pyatv) | None — Bonjour discovery |
| `jarvis-device-zwave` | Z-Wave lights, switches, locks, thermostats | WebSocket (Z-Wave JS UI) | Z-Wave USB stick + Z-Wave JS UI running with WS Server enabled |

### Platform Integrations

For homes already using Home Assistant, the `jarvis-home-assistant-integration` package provides a full device manager (all HA entities), voice commands for device control and status queries, and a background agent for state caching. Requires a long-lived HA access token.

## Getting Started

- To integrate a platform that already has device lists, see [Device Managers](managers.md).
- To add direct control for a new protocol or device family, see [Device Protocols](protocols.md).
- For how plugins are found at runtime, see the [Discovery System](../discovery.md).
