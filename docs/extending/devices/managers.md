# Device Managers

> **The Stewards** --- Device managers are the head stewards who maintain the master inventory of every device in the household. They know what is installed, where it lives, and whether it is online --- whether they learned that from an external authority like Home Assistant or by dispatching their own translators to survey each room.

A device manager implements `IJarvisDeviceManager` to give Jarvis the list of devices from a backend platform. It ships in a package and runs on the Python node, which finds it at startup. The household picks the active manager with the server setting `smart_home.device_manager`.

## Interface reference

From the SDK (`jarvis_command_sdk/device_manager.py`):

```python
from abc import ABC, abstractmethod

from jarvis_command_sdk import AuthenticationConfig, DeviceManagerDevice, IJarvisSecret


class IJarvisDeviceManager(ABC):
    # --- Required (abstract) ---

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier, e.g. 'home_assistant', 'jarvis_direct'."""

    @property
    @abstractmethod
    def friendly_name(self) -> str:
        """Label shown in the mobile app, e.g. 'Home Assistant'."""

    @property
    @abstractmethod
    def can_edit_devices(self) -> bool:
        """True: the mobile app lets the user curate the device list."""

    @abstractmethod
    async def collect_devices(self) -> list[DeviceManagerDevice]:
        """Return the current list of devices from this backend."""

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
```

The node's own copy of the interface (`core/ijarvis_device_manager.py`, used by the built-in `jarvis_direct`) adds `is_available()` and `validate_secrets()`, which returns the keys of missing required secrets. They are not part of the SDK interface; a package doesn't implement them.

## Key properties

### `can_edit_devices`

Whether the mobile app shows a device curation UI:

- **`True`** (Jarvis Direct): the manager finds everything it can, and the user chooses which devices to keep.
- **`False`** (Home Assistant): the platform is the source of truth. Jarvis imports what it exposes and allows no local edits.

### `required_secrets` and `authentication`

A manager that needs credentials declares them as `JarvisSecret`s in `required_secrets`, and optionally an `AuthenticationConfig` for an OAuth sign-in. The mobile app shows them on the node's settings screen (see [Settings Snapshots](../infrastructure/settings.md)). Read them with `JarvisStorage` when you need them, and handle a value that isn't set yet.

## Implementations

### Jarvis Direct (built into the node)

`device_managers/jarvis_direct_manager.py` in `jarvis-node-setup`, name `jarvis_direct`, `can_edit_devices = True`. It is the "no hub" option: it runs `discover()` on every installed [device protocol](protocols.md) at once and merges the results:

```python
# What JarvisDirectDeviceManager.collect_devices() does (simplified)
families = get_device_family_discovery_service().get_all_families()
protocols = list(families.values())
results = await asyncio.gather(
    *[p.discover(timeout=SCAN_TIMEOUT) for p in protocols],
    return_exceptions=True,
)
```

A protocol that fails is logged and skipped. When several protocols find the same device, it keeps one, matching on (in order):

1. **MAC address** (same hardware)
2. **IP address** (same network endpoint)
3. **Cloud ID** (same vendor account)
4. **Entity ID** (fallback)

and converts each `DiscoveredDevice` to a `DeviceManagerDevice` with `source="direct"`.

### Home Assistant (a package)

The Home Assistant manager comes from the [`jarvis-home-assistant-integration`](https://github.com/alexberardi/jarvis-home-assistant-integration) package, not from the node. Its manager, `home_assistant` (`can_edit_devices = False`), reads the devices and entities from your Home Assistant instance and maps each entity to a `DeviceManagerDevice` with `source="home_assistant"`. It needs `HOME_ASSISTANT_REST_URL` and `HOME_ASSISTANT_API_KEY` (a long-lived access token), and also offers an OAuth sign-in. The same package has the Home Assistant commands and an agent.

## Discovery

At startup the node loads every manager in `device_managers/` (the built-in one) and in `device_managers/custom_managers/<package>/`, where the installer puts a package's `manager.py`. A built-in manager whose `validate_secrets()` reports missing keys is skipped. The node loads components once, so restart it after installing one.

See [Discovery System](../discovery.md) for details.

## Writing a custom manager

Start from the scaffold, which writes `manager.py` and the manifest:

```bash
jdt init my_hub --type manager
```

Here is a minimal manager for a hypothetical SmartThings integration:

```python
import httpx

from jarvis_command_sdk import (
    DeviceManagerDevice,
    IJarvisDeviceManager,
    IJarvisSecret,
    JarvisSecret,
    JarvisStorage,
)

CATEGORY_DOMAINS = {"Light": "light", "Switch": "switch", "Thermostat": "climate"}


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
            JarvisSecret("SMARTTHINGS_TOKEN", "Personal access token", "integration", "string",
                         friendly_name="Access token"),
        ]

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        token = JarvisStorage("smartthings").get_secret("SMARTTHINGS_TOKEN")
        if not token:
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.smartthings.com/v1/devices",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            DeviceManagerDevice(
                name=item["label"],
                domain=CATEGORY_DOMAINS.get(item.get("categoryType", ""), "switch"),
                entity_id=f"smartthings.{item['deviceId']}",
                manufacturer=item.get("manufacturerName"),
                model=item.get("name"),
                protocol="smartthings",
                cloud_id=item["deviceId"],
                source="smartthings",
                area=item.get("roomId"),
            )
            for item in data.get("items", [])
        ]
```

`httpx` is installed on the Python node. If your manager needs a library the node doesn't have, declare it in the manifest's `packages`.

Test it with `jdt test`, install it on a node with [`jdt deploy`](../toolkit/deploy.md) (or publish it to Pantry and install it from the mobile app), then restart the node. When the server asks the node for a device list, it names the manager to run (the household's `smart_home.device_manager` setting, `jarvis_direct` by default), or `all` to merge every loaded manager; a manager the node hasn't loaded gets "not found or not configured".
