# Device Protocols

> **The Translators** --- Device protocols are the staff members who speak each device's native language. One translator knows how to talk to LIFX bulbs over UDP. Another knows the Govee cloud API. The steward dispatches them to discover and control devices, but the translator handles the actual conversation with hardware.

A device protocol implements the SDK's `IJarvisDeviceProtocol` to discover and control one device family over the LAN or a cloud API. It ships in a package and runs on the Python node, which finds it at startup.

Protocols are the low-level layer: they talk to hardware. The node's built-in Jarvis Direct manager gathers every installed protocol into one device list (see [Device Managers](managers.md#jarvis-direct-built-into-the-node)).

## Interface reference

From the SDK (`jarvis_command_sdk/device_protocol.py`):

```python
from abc import ABC, abstractmethod
from typing import Any, Literal

from jarvis_command_sdk import (
    AuthenticationConfig,
    DeviceControlResult,
    DiscoveredDevice,
    IJarvisButton,
    IJarvisSecret,
)


class IJarvisDeviceProtocol(ABC):
    # --- Required (abstract) ---

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Short identifier, e.g. 'lifx', 'kasa', 'govee'."""

    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """HA-style domains it controls, e.g. ['light'] or ['light', 'switch']."""

    @abstractmethod
    async def discover(self, timeout: float = 5.0) -> list[DiscoveredDevice]:
        """Scan the network or cloud for devices, within about `timeout` seconds."""

    @abstractmethod
    async def control(
        self, ip: str, action: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> DeviceControlResult:
        """Send a control action to a device."""

    @abstractmethod
    async def get_state(self, ip: str, **kwargs: Any) -> dict[str, Any] | None:
        """Current state of a device, or None if unavailable."""

    # --- Optional (with defaults) ---

    @property
    def connection_type(self) -> Literal["lan", "cloud", "hybrid"]:
        return "lan"

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return []

    @property
    def friendly_name(self) -> str:
        return self.protocol_name.replace("_", " ").title()

    @property
    def description(self) -> str:
        return ""

    @property
    def authentication(self) -> AuthenticationConfig | None:
        return None

    @property
    def supported_actions(self) -> list[IJarvisButton]:
        """Buttons shown for the device. Default: Turn On / Turn Off."""
        return [
            IJarvisButton("Turn On", "turn_on", "primary", "power"),
            IJarvisButton("Turn Off", "turn_off", "secondary", "power-off"),
        ]

    def store_auth_values(self, values: dict[str, str]) -> None:
        """Called with the values from an OAuth/auth flow, to persist them."""

    async def on_removed(self, device: Any, **kwargs: Any) -> None:
        """Called when a device of this protocol is removed. Default: no-op."""

    async def get_stream_source(self, device: DiscoveredDevice) -> str | None:
        """Camera stream source. Not used on jarvisd yet; see below."""
        return None
```

!!! warning "`discover()` must take `timeout`"
    The node always calls `discover(timeout=...)`. A protocol whose `discover()` has no `timeout` parameter raises `TypeError` on every scan, and because the scans run together with errors collected, the protocol silently finds no devices. Keep the signature `async def discover(self, timeout: float = 5.0)`.

**What the node passes to `control()` and `get_state()`.** Despite the parameter name, the node calls `control()` with the device's `DiscoveredDevice` as the first argument (rebuilt from the device registry: `entity_id`, `name`, `domain`, `protocol`, `cloud_id`, `local_ip`, `mac_address`), then the action and the `data` dict. It calls `get_state()` with `ip=` the device's local IP (possibly empty) and keyword arguments such as `entity_id`, `cloud_id`, `mac_address` and sometimes `device`. Read what you need defensively, as the [Hue package](https://github.com/alexberardi/jarvis-device-hue/blob/main/device_families/hue/protocol.py) does.

The node's own copy of the interface (`device_families/base.py`, used by node code) adds `validate_secrets()`, which returns the keys of missing required secrets. It is not part of the SDK interface.

### `on_removed`: device deletion hook { #on_removed-device-deletion-hook-sdk-v042 }

When a device is deleted, your Jarvis Automation server sends the owning node a `device_removed` command (for node-managed devices, `source="direct"`, only). The node calls `on_removed(device, entity_id=...)` on the protocol, where `device` is a `DiscoveredDevice`, before the record goes. Use it to release anything tied to the device:

```python
async def on_removed(self, device: Any, **kwargs: Any) -> None:
    # Release any external resource (e.g. unpair, revoke a token)
    await self._sessions.release(device.entity_id)
```

- **Best-effort:** a failure is logged as a warning and the delete goes ahead.
- **Default:** no-op. Needs SDK 0.4.2 or later.

### `get_stream_source`: camera streaming (not on jarvisd yet) { #get_stream_source-camera-streaming-hook-sdk-v050 }

!!! note "Not available on jarvisd"
    Camera streaming is deferred on jarvisd: every streaming route answers "Camera streaming is not available in this version", and nothing calls `get_stream_source()`. Camera devices still appear in the device list.

The hook stays in the SDK (0.5.0+) for when streaming returns: a protocol returns a stream source string for a camera device, or `None`. The [`jarvis-device-nest`](https://github.com/alexberardi/jarvis-device-nest) package implements it.

### `needs_pairing`: pairing state

When `get_state()` returns `{"needs_pairing": True}`, the node reports the device as needing pairing before any domain normalization:

```python
{
    "entity_id": ...,
    "domain": ...,
    "state": {"needs_pairing": True},
    "ui_hints": {"control_type": "pairing"},
}
```

The mobile app then shows a **Pair** action (a setup-code or PIN dialog) instead of the normal controls. Once pairing succeeds, return the real state. Use it for protocols that need an out-of-band pairing step, such as HomeKit setup codes:

```python
async def get_state(self, ip: str, **kwargs: Any) -> dict[str, Any] | None:
    if not self._is_paired(kwargs.get("entity_id", "")):
        return {"needs_pairing": True}
    return {"on": True, "brightness": 80}
```

For a PIN or pairing step inside `control()`, return a `DeviceControlResult` with `input_required` (below).

## Supporting dataclasses

### DiscoveredDevice

Returned by `discover()`:

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiscoveredDevice:
    name: str                          # "Living Room Bulb"
    domain: str                        # "light", "switch", "media_player"
    manufacturer: str                  # "LIFX", "TP-Link"
    model: str                         # "A19", "KP125"
    protocol: str                      # "lifx", "kasa"
    entity_id: str                     # "lifx.d073d5xxxxxx"
    local_ip: str | None = None        # "192.168.1.42"
    mac_address: str | None = None     # "D0:73:D5:XX:XX:XX"
    cloud_id: str | None = None        # the vendor's device ID
    device_class: str | None = None    # "outlet", "dimmer", ...
    is_controllable: bool = True
    extra: dict[str, Any] = field(default_factory=dict)  # protocol-specific metadata
```

### DeviceControlResult and InputRequest

Returned by `control()`:

```python
from dataclasses import dataclass


@dataclass
class InputRequest:
    type: str                                 # "pin", "text" or "confirm"
    prompt: str                               # "Enter the PIN shown on your Apple TV"
    session_id: str                           # opaque ID for the follow-up action
    follow_up_action: str = "pair_finish"     # the action the app sends back


@dataclass
class DeviceControlResult:
    success: bool
    entity_id: str
    action: str                               # "turn_on", "set_brightness", ...
    error: str | None = None                  # why it failed
    input_required: InputRequest | None = None
```

With `input_required` set, the mobile app shows a dialog of that type, then calls `control()` again with `follow_up_action` and the user's answer.

## Example packages

The node ships no protocols of its own (its `device_families/` holds only `base.py`, `domains/` and `custom_families/`). Protocols come from packages, for example:

| Package | Protocol | Connection | Secrets |
|---------|----------|------------|---------|
| [`jarvis-device-lifx`](https://github.com/alexberardi/jarvis-device-lifx) | LIFX bulbs | LAN (UDP 56700) | None |
| [`jarvis-device-kasa`](https://github.com/alexberardi/jarvis-device-kasa) | TP-Link Kasa / Tapo | LAN broadcast | None |
| [`jarvis-device-govee`](https://github.com/alexberardi/jarvis-device-govee) | Govee lights and plugs | Hybrid (LAN + cloud) | `GOVEE_API_KEY` |
| [`jarvis-device-hue`](https://github.com/alexberardi/jarvis-device-hue) | Philips Hue | LAN (Hue Bridge) | `HUE_BRIDGE_IP`, `HUE_USERNAME` |
| [`jarvis-device-apple`](https://github.com/alexberardi/jarvis-device-apple) | Apple TV, HomePod | LAN (mDNS, `pyatv`) | None (pairing) |

See [Device Control](index.md#available-device-packages) for the full list.

## Discovery

The installer puts a package's `protocol.py` in `device_families/custom_families/<package>/`. At startup the node loads every protocol there. It loads components once, so restart the node after installing one.

See [Discovery System](../discovery.md) for details.

## Writing a custom protocol

Start from the scaffold, which writes `protocol.py` and the manifest:

```bash
jdt init my_lights --type protocol
```

Here is a minimal protocol for Hue lights through the local Hue Bridge API (the real [`jarvis-device-hue`](https://github.com/alexberardi/jarvis-device-hue) does more):

```python
from typing import Any

import httpx

from jarvis_command_sdk import (
    DeviceControlResult,
    DiscoveredDevice,
    IJarvisDeviceProtocol,
    IJarvisSecret,
    JarvisSecret,
    JarvisStorage,
)

_storage = JarvisStorage("hue")


class HueProtocol(IJarvisDeviceProtocol):
    @property
    def protocol_name(self) -> str:
        return "hue"

    @property
    def supported_domains(self) -> list[str]:
        return ["light"]

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return [
            JarvisSecret("HUE_BRIDGE_IP", "Hue Bridge IP address", "integration", "string",
                         is_sensitive=False, friendly_name="Bridge IP"),
            JarvisSecret("HUE_USERNAME", "Hue Bridge API username", "integration", "string",
                         friendly_name="API username"),
        ]

    def _bridge(self) -> tuple[str | None, str | None]:
        return _storage.get_secret("HUE_BRIDGE_IP"), _storage.get_secret("HUE_USERNAME")

    async def discover(self, timeout: float = 5.0) -> list[DiscoveredDevice]:
        bridge_ip, username = self._bridge()
        if not bridge_ip or not username:
            return []
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"http://{bridge_ip}/api/{username}/lights")
            resp.raise_for_status()
            lights = resp.json()

        return [
            DiscoveredDevice(
                name=light["name"],
                domain="light",
                manufacturer=light.get("manufacturername", "Philips"),
                model=light.get("modelid", "Unknown"),
                protocol="hue",
                entity_id=f"light.hue_{light_id}",
                local_ip=bridge_ip,
                cloud_id=light_id,  # the bridge's light ID
            )
            for light_id, light in lights.items()
        ]

    async def control(
        self, ip: Any, action: str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> DeviceControlResult:
        # The node passes the DiscoveredDevice as the first argument.
        entity_id = getattr(ip, "entity_id", "") or kwargs.get("entity_id", "")
        light_id = getattr(ip, "cloud_id", None) or (data or {}).get("cloud_id")
        bridge_ip, username = self._bridge()
        if not (bridge_ip and username and light_id):
            return DeviceControlResult(False, entity_id, action, error="Hue bridge not configured")

        if action == "turn_on":
            payload: dict[str, Any] = {"on": True}
        elif action == "turn_off":
            payload = {"on": False}
        elif action == "set_brightness":
            bri = int((data or {}).get("brightness", 100) / 100 * 254)  # Hue uses 1-254
            payload = {"on": True, "bri": max(1, bri)}
        else:
            return DeviceControlResult(False, entity_id, action, error=f"Unsupported action: {action}")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.put(
                    f"http://{bridge_ip}/api/{username}/lights/{light_id}/state", json=payload
                )
                resp.raise_for_status()
        except httpx.HTTPError as e:
            return DeviceControlResult(False, entity_id, action, error=str(e))
        return DeviceControlResult(True, entity_id, action)

    async def get_state(self, ip: str, **kwargs: Any) -> dict[str, Any] | None:
        light_id = kwargs.get("cloud_id") or getattr(kwargs.get("device"), "cloud_id", None)
        bridge_ip, username = self._bridge()
        if not (bridge_ip and username and light_id):
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"http://{bridge_ip}/api/{username}/lights/{light_id}")
                resp.raise_for_status()
                state = resp.json()["state"]
        except (httpx.HTTPError, KeyError):
            return None
        return {
            "on": state["on"],
            "brightness": int(state.get("bri", 0) / 254 * 100),
            "reachable": state.get("reachable", False),
        }
```

`httpx` is installed on the Python node; declare any other library in the manifest's `packages` (as `- name: <package>`). Test it with `jdt test`, install it on a node with [`jdt deploy`](../toolkit/deploy.md) (or publish it to Pantry and install it from the mobile app), then restart the node.
