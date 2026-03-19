# Device Protocols

> **The Translators** --- Device protocols are the staff members who speak each device's native language. One translator knows how to talk to LIFX bulbs over UDP. Another knows the Govee cloud API. The steward dispatches them to discover and control devices, but the translator handles the actual conversation with hardware.

A device protocol implements the `IJarvisDeviceProtocol` interface (from `device_families/base.py`) to provide direct LAN or cloud control of a specific device family. Protocols are discovered automatically by `DeviceFamilyDiscoveryService` at startup.

Protocols are the low-level layer --- they talk to hardware. The `JarvisDirectDeviceManager` aggregates all protocols into a unified device list.

## Interface Reference

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class IJarvisDeviceProtocol(ABC):
    # --- Required (abstract) ---

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Unique protocol identifier. Examples: 'lifx', 'kasa', 'govee'."""
        ...

    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """HA-style domains this protocol can control. Examples: ['light'], ['light', 'switch']."""
        ...

    @abstractmethod
    async def discover(self) -> list[DiscoveredDevice]:
        """Scan the network/cloud for devices this protocol can control."""
        ...

    @abstractmethod
    async def control(
        self, ip: str, action: str, data: dict | None = None, **kwargs
    ) -> DeviceControlResult:
        """Send a control command to a device."""
        ...

    @abstractmethod
    async def get_state(self, ip: str, **kwargs) -> dict | None:
        """Query the current state of a device. Returns None if unavailable."""
        ...

    # --- Optional (with defaults) ---

    @property
    def connection_type(self) -> str:
        """'lan', 'cloud', or 'hybrid'. Default: 'lan'."""
        return "lan"

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return []

    @property
    def friendly_name(self) -> str:
        return self.protocol_name.title()

    @property
    def description(self) -> str:
        return ""

    @property
    def authentication(self) -> AuthenticationConfig | None:
        return None

    @property
    def supported_actions(self) -> list[IJarvisButton]:
        """Default actions: turn_on, turn_off."""
        return [
            IJarvisButton(action="turn_on", label="Turn On"),
            IJarvisButton(action="turn_off", label="Turn Off"),
        ]

    def store_auth_values(self, values: dict) -> None:
        """Called after OAuth/auth flow completes to persist credentials."""
        ...

    def validate_secrets(self) -> list[str]:
        """Returns a list of validation error messages (empty = valid)."""
        ...
```

## Supporting Dataclasses

### DiscoveredDevice

Returned by `discover()`. Contains everything Jarvis needs to identify and control a device:

```python
@dataclass
class DiscoveredDevice:
    name: str                    # "Living Room Bulb"
    domain: str                  # "light", "switch", "media_player"
    manufacturer: str            # "LIFX", "TP-Link"
    model: str                   # "A19", "KP125"
    protocol: str                # "lifx", "kasa"
    entity_id: str               # "lifx.d073d5xxxxxx"
    local_ip: str | None         # "192.168.1.42"
    mac_address: str | None      # "D0:73:D5:XX:XX:XX"
    cloud_id: str | None         # Vendor-specific cloud ID
    device_class: str | None     # "outlet", "dimmer", etc.
    is_controllable: bool        # True if Jarvis can send commands
    extra: dict | None           # Protocol-specific metadata
```

### DeviceControlResult

Returned by `control()`. Indicates success or failure:

```python
@dataclass
class DeviceControlResult:
    success: bool        # Did the command succeed?
    entity_id: str       # Which device was targeted
    action: str          # What action was attempted ("turn_on", "set_brightness")
    error: str | None    # Error message if success=False
```

## Built-in Protocols

### LIFX Protocol

**Connection:** LAN UDP on port 56700
**Library:** `lifxlan`
**Secrets:** None (discovery is broadcast-based)
**Domains:** `["light"]`

```python
class LifxProtocol(IJarvisDeviceProtocol):
    protocol_name = "lifx"
    supported_domains = ["light"]
    connection_type = "lan"

    async def discover(self) -> list[DiscoveredDevice]:
        # Uses lifxlan.LifxLAN() to broadcast discovery on UDP 56700
        # Returns all LIFX bulbs found on the local network
        ...

    async def control(self, ip, action, data=None, **kwargs):
        # Supported actions: turn_on, turn_off, set_brightness
        # Brightness: 0-100 (user-facing) mapped to 0-65535 (LIFX protocol)
        ...
```

**Brightness mapping:** LIFX uses a 0--65535 range internally. The protocol adapter maps the user-facing 0--100 scale:

```python
lifx_brightness = int(brightness_percent / 100 * 65535)
```

### Kasa Protocol

**Connection:** LAN broadcast
**Library:** `python-kasa`
**Secrets:** None (local discovery)
**Domains:** `["light", "switch"]`

```python
class KasaProtocol(IJarvisDeviceProtocol):
    protocol_name = "kasa"
    supported_domains = ["light", "switch"]
    connection_type = "lan"

    async def discover(self) -> list[DiscoveredDevice]:
        # Uses kasa.Discover.discover() for LAN broadcast
        # Maps Kasa device types to HA-style domains:
        #   SmartBulb -> "light"
        #   SmartPlug -> "switch"
        #   SmartDimmer -> "light"
        ...

    async def control(self, ip, action, data=None, **kwargs):
        # Connects to device by IP, sends turn_on/turn_off/set_brightness
        ...
```

**Device type mapping:** Kasa has its own device taxonomy. The protocol maps these to HA-style domains:

| Kasa Type | HA Domain |
|-----------|-----------|
| `SmartBulb` | `light` |
| `SmartPlug` | `switch` |
| `SmartDimmer` | `light` |
| `SmartStrip` | `switch` |
| `SmartSwitch` | `switch` |

### Govee Protocol

**Connection:** Hybrid (LAN + cloud REST API)
**Library:** `httpx`
**Secrets:** `GOVEE_API_KEY` (required for cloud API)
**Domains:** `["light"]`

```python
class GoveeProtocol(IJarvisDeviceProtocol):
    protocol_name = "govee"
    supported_domains = ["light"]
    connection_type = "hybrid"

    required_secrets = [
        IJarvisSecret(key="GOVEE_API_KEY", description="Govee Developer API key"),
    ]

    async def discover(self) -> list[DiscoveredDevice]:
        # Calls Govee cloud API: GET https://developer-api.govee.com/v1/devices
        # Returns device list with capabilities
        ...

    async def control(self, ip, action, data=None, **kwargs):
        # Dual API fallback:
        # 1. Try LAN control first (faster, no rate limits)
        # 2. Fall back to cloud REST API if LAN fails
        #
        # Capability-based payloads:
        #   {"device": "...", "model": "...", "cmd": {"name": "turn", "value": "on"}}
        ...
```

**Dual API fallback:** Govee devices that support LAN control receive commands directly over the local network. If LAN control fails (device not on same subnet, firmware limitation), the protocol falls back to the cloud REST API transparently.

**Capability-based payloads:** Govee devices report their capabilities via the API. The protocol checks capabilities before sending commands --- for example, only devices with the `brightness` capability receive brightness commands.

### Apple Protocol

**Connection:** mDNS / Bonjour
**Library:** `pyatv`
**Secrets:** None (mDNS discovery + pairing)
**Domains:** `["media_player"]`

```python
class AppleProtocol(IJarvisDeviceProtocol):
    protocol_name = "apple"
    supported_domains = ["media_player"]
    connection_type = "lan"

    async def discover(self) -> list[DiscoveredDevice]:
        # Uses pyatv.scan() for mDNS/Bonjour discovery
        # Filters by model whitelist (Apple TV, HomePod)
        ...

    async def control(self, ip, action, data=None, **kwargs):
        # Supported actions: turn_on, turn_off, play, pause, next, previous
        # Uses pyatv RemoteControl protocol
        ...
```

**Model whitelist:** The Apple protocol only reports devices matching a known model list (Apple TV 4K, Apple TV HD, HomePod, HomePod mini). This avoids exposing every AirPlay-capable device on the network as a controllable device.

## Discovery

Protocols are discovered by `DeviceFamilyDiscoveryService`, which scans the `device_families/` package at startup:

```
device_families/
    __init__.py
    base.py                        # IJarvisDeviceProtocol ABC + dataclasses
    lifx_protocol.py
    kasa_protocol.py
    govee_protocol.py
    apple_protocol.py
    your_new_protocol.py           # <-- just add the file
```

See [Discovery System](../discovery.md) for details.

## Writing a Custom Protocol

Here is a minimal example for controlling Hue bulbs over the local Hue Bridge API:

```python
from device_families.base import IJarvisDeviceProtocol, DiscoveredDevice, DeviceControlResult
from core.interfaces import IJarvisSecret

class HueProtocol(IJarvisDeviceProtocol):
    @property
    def protocol_name(self) -> str:
        return "hue"

    @property
    def supported_domains(self) -> list[str]:
        return ["light"]

    @property
    def connection_type(self) -> str:
        return "lan"

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return [
            IJarvisSecret(key="HUE_BRIDGE_IP", description="Hue Bridge IP address"),
            IJarvisSecret(key="HUE_USERNAME", description="Hue Bridge API username"),
        ]

    async def discover(self) -> list[DiscoveredDevice]:
        bridge_ip = self.secret_service.get_secret("HUE_BRIDGE_IP")
        username = self.secret_service.get_secret("HUE_USERNAME")

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://{bridge_ip}/api/{username}/lights")
            resp.raise_for_status()
            lights = resp.json()

        devices: list[DiscoveredDevice] = []
        for light_id, light in lights.items():
            devices.append(DiscoveredDevice(
                name=light["name"],
                domain="light",
                manufacturer=light.get("manufacturername", "Philips"),
                model=light.get("modelid", "Unknown"),
                protocol="hue",
                entity_id=f"hue.{light_id}",
                local_ip=bridge_ip,
                mac_address=light.get("uniqueid"),
                cloud_id=None,
                device_class="light",
                is_controllable=True,
                extra={"light_id": light_id},
            ))
        return devices

    async def control(
        self, ip: str, action: str, data: dict | None = None, **kwargs
    ) -> DeviceControlResult:
        light_id = kwargs.get("entity_id", "").split(".")[-1]
        username = self.secret_service.get_secret("HUE_USERNAME")

        payload: dict = {}
        if action == "turn_on":
            payload = {"on": True}
        elif action == "turn_off":
            payload = {"on": False}
        elif action == "set_brightness":
            # Hue uses 1-254 range
            bri = int((data or {}).get("brightness", 100) / 100 * 254)
            payload = {"on": True, "bri": max(1, bri)}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"http://{ip}/api/{username}/lights/{light_id}/state",
                    json=payload,
                )
                resp.raise_for_status()
            return DeviceControlResult(
                success=True, entity_id=f"hue.{light_id}", action=action, error=None
            )
        except Exception as e:
            return DeviceControlResult(
                success=False, entity_id=f"hue.{light_id}", action=action, error=str(e)
            )

    async def get_state(self, ip: str, **kwargs) -> dict | None:
        light_id = kwargs.get("entity_id", "").split(".")[-1]
        username = self.secret_service.get_secret("HUE_USERNAME")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://{ip}/api/{username}/lights/{light_id}")
                resp.raise_for_status()
                data = resp.json()
            return {
                "on": data["state"]["on"],
                "brightness": int(data["state"].get("bri", 0) / 254 * 100),
                "reachable": data["state"]["reachable"],
            }
        except Exception:
            return None
```

Save as `device_families/hue_protocol.py` and restart the node.
