# Device Managers

> **The Stewards** --- Device managers are the head stewards who maintain the master inventory of every device in the household. They know what is installed, where it lives, and whether it is online --- whether they learned that from an external authority like Home Assistant or by dispatching their own translators to survey each room.

A device manager implements `IJarvisDeviceManager` to provide Jarvis with a list of controllable devices from a backend platform. Managers are discovered automatically by `DeviceManagerDiscoveryService` at startup.

## Interface Reference

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class IJarvisDeviceManager(ABC):
    # --- Required (abstract) ---

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier. Examples: 'home_assistant', 'jarvis_direct'."""
        ...

    @property
    @abstractmethod
    def friendly_name(self) -> str:
        """Human-readable label shown in the mobile app. Examples: 'Home Assistant', 'Jarvis Direct'."""
        ...

    @property
    @abstractmethod
    def can_edit_devices(self) -> bool:
        """If True, the mobile app shows an edit UI for curating the device list."""
        ...

    @abstractmethod
    async def collect_devices(self) -> list[DeviceManagerDevice]:
        """Return the current list of devices from this backend."""
        ...

    # --- Optional (with defaults) ---

    @property
    def description(self) -> str:
        return ""

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return []

    @property
    def authentication(self) -> AuthenticationConfig | None:
        return None

    def is_available(self) -> bool:
        """Returns True if all required secrets are present. Called by discovery."""
        ...

    def validate_secrets(self) -> list[str]:
        """Returns a list of validation error messages (empty = valid)."""
        ...
```

## Key Properties

### `can_edit_devices`

This property controls whether the mobile app presents a device curation UI:

- **`True`** (Jarvis Direct) --- The user manually adds/removes devices from the discovered list. The manager discovers everything it can find on the network, but only user-selected devices are active.
- **`False`** (Home Assistant) --- The external platform is the source of truth. Jarvis imports whatever HA exposes and does not allow local edits.

### `required_secrets` and `authentication`

Managers that need credentials declare them via `required_secrets` (a list of `IJarvisSecret` objects) and optionally `authentication` (an `AuthenticationConfig` for OAuth flows). If secrets are missing, `is_available()` returns `False` and the manager is skipped at discovery time.

## Built-in Implementations

### HomeAssistantDeviceManager

Connects to a Home Assistant instance via WebSocket and maps HA entities to `DeviceManagerDevice` objects.

```python
class HomeAssistantDeviceManager(IJarvisDeviceManager):
    name = "home_assistant"
    friendly_name = "Home Assistant"
    can_edit_devices = False  # HA is the source of truth

    required_secrets = [
        IJarvisSecret(key="HA_REST_URL", description="Home Assistant URL"),
        IJarvisSecret(key="HA_API_KEY", description="Long-lived access token"),
    ]

    authentication = AuthenticationConfig(
        # OAuth config for HA authentication flow
        ...
    )

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        # 1. Connect to HA WebSocket
        # 2. Fetch entity registry
        # 3. Map each entity to DeviceManagerDevice
        # 4. Filter to supported domains (light, switch, climate, etc.)
        ...
```

**What it does:**

- Opens a WebSocket connection to the HA instance
- Fetches the full entity registry
- Maps HA entity attributes (friendly_name, device_class, state) to the normalized `DeviceManagerDevice` format
- Requires `HA_REST_URL` and `HA_API_KEY` secrets
- Includes an OAuth `AuthenticationConfig` for token-based authentication

### JarvisDirectDeviceManager

Aggregates all discovered `IJarvisDeviceProtocol` adapters into a single device list. This is the "no hub needed" option --- Jarvis talks directly to devices over LAN or cloud APIs.

```python
class JarvisDirectDeviceManager(IJarvisDeviceManager):
    name = "jarvis_direct"
    friendly_name = "Jarvis Direct"
    can_edit_devices = True  # User curates the device list

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        # 1. Get all registered IJarvisDeviceProtocol instances
        # 2. Call discover() on each protocol concurrently
        protocols = get_device_family_discovery_service().get_all_protocols()
        tasks = [proto.discover() for proto in protocols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Flatten and deduplicate
        all_devices = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Protocol discovery failed: {result}")
                continue
            all_devices.extend(result)

        return self._deduplicate(all_devices)
```

**Deduplication logic:** When the same physical device is discovered by multiple protocols, `JarvisDirectDeviceManager` deduplicates using a priority chain:

1. **MAC address** (strongest --- same hardware)
2. **IP address** (same network endpoint)
3. **Cloud ID** (same vendor account)
4. **Entity ID** (fallback)

## Discovery

Managers are discovered by `DeviceManagerDiscoveryService`, which scans the `device_managers/` package at startup. Place your manager file in that directory and it is registered automatically:

```
device_managers/
    __init__.py
    home_assistant_device_manager.py
    jarvis_direct_device_manager.py
    your_new_manager.py              # <-- just add the file
```

See [Discovery System](../discovery.md) for details on how scanning works.

## Settings Sync

The function `get_all_managers_for_snapshot()` collects metadata from all registered managers (including those that are unavailable due to missing secrets). This is used by the settings sync system to show all possible managers in the mobile app, so users can configure secrets for managers they want to enable.

```python
def get_all_managers_for_snapshot() -> list[dict]:
    """Return manager metadata for settings sync. No secret filtering."""
    managers = get_device_manager_discovery_service().get_all_managers()
    return [
        {
            "name": m.name,
            "friendly_name": m.friendly_name,
            "can_edit_devices": m.can_edit_devices,
            "is_available": m.is_available(),
            "required_secrets": [s.key for s in m.required_secrets],
            "authentication": m.authentication.to_dict() if m.authentication else None,
        }
        for m in managers
    ]
```

## Writing a Custom Manager

Here is a minimal example that integrates a hypothetical SmartThings hub:

```python
from device_managers.base import IJarvisDeviceManager, DeviceManagerDevice
from core.interfaces import IJarvisSecret

class SmartThingsDeviceManager(IJarvisDeviceManager):
    @property
    def name(self) -> str:
        return "smartthings"

    @property
    def friendly_name(self) -> str:
        return "SmartThings"

    @property
    def can_edit_devices(self) -> bool:
        return False  # SmartThings is the source of truth

    @property
    def description(self) -> str:
        return "Samsung SmartThings hub integration"

    @property
    def required_secrets(self) -> list[IJarvisSecret]:
        return [
            IJarvisSecret(key="SMARTTHINGS_TOKEN", description="Personal access token"),
        ]

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        token = self.secret_service.get_secret("SMARTTHINGS_TOKEN")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.smartthings.com/v1/devices",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        devices: list[DeviceManagerDevice] = []
        for item in data["items"]:
            devices.append(DeviceManagerDevice(
                name=item["label"],
                domain=self._map_category(item["categoryType"]),
                entity_id=f"smartthings.{item['deviceId']}",
                is_controllable=True,
                manufacturer=item.get("manufacturerName", "Unknown"),
                model=item.get("name", "Unknown"),
                protocol="smartthings",
                local_ip=None,
                mac_address=None,
                cloud_id=item["deviceId"],
                area=item.get("roomId"),
                state=None,
                extra=None,
            ))
        return devices

    def _map_category(self, category: str) -> str:
        mapping = {"Light": "light", "Switch": "switch", "Thermostat": "climate"}
        return mapping.get(category, "switch")
```

Save this as `device_managers/smartthings_device_manager.py` and restart the node. The discovery service picks it up automatically.
