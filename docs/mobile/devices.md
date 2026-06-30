# Devices

The Devices tab shows all smart home devices discovered in your household. Devices are found through installed device protocol packages (Kasa, LIFX, Govee, Apple, Nest, Home Assistant).

## Device List

Devices are grouped by room. Each device shows:

- Device name
- Domain (light, switch, climate, media_player)
- Current state (on/off)
- Protocol source (kasa, lifx, govee, etc.)

Tap a device to view details and control it.

## Device Discovery

New devices are discovered automatically when a device protocol package is installed and the node scans the network. You can trigger a manual scan from the **Devices** tab.

When you start a scan, Jarvis targets the household's **primary node** — the node designated for device discovery in your Smart Home settings. If no primary node is configured, it falls back to the first available node. This ensures discovery runs on the node that actually has the relevant protocol installed (for example, a Pi with a HomeKit package), rather than whichever node happens to sort first.

## Pairing a Device

Some protocols require a pairing step before a device can be controlled — for example, HomeKit accessories must complete a PIN-based HAP handshake before Jarvis can drive them. These devices show a **Pair** button instead of a domain control panel.

**To pair:**

1. Tap the device in the Devices list.
2. On the device detail screen, tap **Pair HomeKit device**.
3. Enter the setup code when prompted (typically printed on the accessory or shown in its companion app).
4. Tap **Submit**. A "Pairing…" spinner is shown while the handshake is in flight.
5. Once pairing succeeds, the panel flips automatically to the domain control (e.g. thermostat) — no manual refresh needed.

If pairing fails, an alert is shown with the error. Email + password or another attempt can be retried immediately.

## Smart Home Setup

Configure your smart home integration from **Settings > Smart Home**. This includes:

- Selecting a primary node for device discovery
- Enabling external device protocols
- Connecting to Home Assistant (if available)
