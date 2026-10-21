# Command Data Store

Commands that keep state between runs (a cache, a list, a schedule) store it as key-value records: each record is a JSON-serialisable `dict` under a key, scoped to the command, with an optional expiry. Records survive restarts.

## JarvisStorage (SDK Persistence Facade)

A package stores data with the SDK's `JarvisStorage`. It works on every device that runs packages: on the Python node it writes to the node's encrypted database, and on a computer the desktop agent keeps the data.

```python
from datetime import datetime, timedelta, timezone

from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("my_command")  # your command's name

storage.save("last_result", {"value": 42})
storage.save(
    "cache:Miami",
    {"temp": 75, "condition": "sunny"},
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
)

result = storage.get("last_result")   # {"value": 42}, or None
records = storage.get_all()           # every live record for this command
storage.delete("cache:Miami")         # True if a record was deleted
storage.delete_all()                  # how many were deleted
```

| Method | Does |
|--------|------|
| `save(key, data, expires_at=None)` | Insert or replace the record under `key`. `data` is a `dict`; the store serialises it |
| `get(key)` | The `dict`, or `None` when there is none or it has expired |
| `get_all()` | Every unexpired record, each with `_data_key` and `_expires_at` added |
| `delete(key)` | Delete one record |
| `delete_all()` | Delete every record of this command |

Expired records are hidden from `get` and `get_all`, but stay in the store until they are deleted or overwritten. Use a timezone-aware `expires_at`.

With no storage backend registered (unit tests, Pantry validation) `get` returns `None`, `get_all` returns `[]` and `save` does nothing.

## Use cases

### Caching API responses

```python
from datetime import datetime, timedelta, timezone

from jarvis_command_sdk import JarvisStorage

CACHE_TTL = timedelta(minutes=30)
storage = JarvisStorage("get_weather")


def get_weather_cached(city: str) -> dict | None:
    return storage.get(f"cache:{city}")  # None once it has expired


def cache_weather(city: str, data: dict) -> None:
    storage.save(f"cache:{city}", data, expires_at=datetime.now(timezone.utc) + CACHE_TTL)
```

### Persistent lists

A record is a `dict`, so wrap a list in one:

```python
from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("shopping_list")


def add_item(item: str) -> None:
    items = (storage.get("items") or {}).get("items", [])
    storage.save("items", {"items": [*items, item]})


def get_items() -> list[str]:
    return (storage.get("items") or {}).get("items", [])
```

### State that ends on its own

A record that expires when its moment passes drops out of `get_all` by itself:

```python
from datetime import datetime

from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("parking")


def remember_meter(spot: str, ends_at: datetime) -> None:
    storage.save(f"meter:{spot}", {"spot": spot, "ends_at": ends_at.isoformat()}, expires_at=ends_at)


def active_meters() -> list[dict]:
    return [r for r in storage.get_all() if r["_data_key"].startswith("meter:")]
```

## Data Browser Protocol

The mobile app's data browser lists, shows, edits and deletes a command's records, over MQTT (the `command-data/` topics). Commands that opt in also let users create records with the **+** button.

### Opting into record creation

Declare support on your command class:

```python
@property
def data_browser_supports_create(self) -> bool:
    return True
```

Commands that leave this `False` (the default) refuse create requests at the node, so a generic save can never bypass runtime state (for example, a scheduler that reads an in-memory cache).

The SDK's default `data_browser_create` then does an owner-stamped save through `JarvisStorage`: it drops any client-supplied `id`, `user_id`, `data_key` and `created_at`, makes a new key, sets `user_id` to the requesting user and refuses a request with no known user. Override it only to apply your own rules:

```python
import uuid
from typing import Any

from jarvis_command_sdk import JarvisStorage


def data_browser_create(
    self,
    fields: dict[str, Any],
    requesting_user_id: int | None,
) -> tuple[str, dict]:
    """Make a new record and return (data_key, record)."""
    if requesting_user_id is None:
        raise ValueError("cannot create a record without a known user")
    if not fields.get("text"):
        raise ValueError("Enter some text first")
    key = uuid.uuid4().hex
    record = {**fields, "id": key, "user_id": requesting_user_id}
    JarvisStorage(self.command_name).save(key, record)
    return key, record
```

The node passes only the **editable and `create_only`** fields; server-managed fields never arrive. Raise `ValueError` to show the user a message (the app gets a 400).

### `FieldSpec.create_only`

Use `create_only=True` for a field that is set when the record is created and fixed after that, such as a scope whose change would alter who can see the record:

```python
from jarvis_command_sdk import FieldSpec

FieldSpec("scope", "enum", enum_values=["personal", "household"],
          editable=False, create_only=True)
```

| Behaviour | `editable=True` | `create_only=True` |
|-----------|----------------|-------------------|
| Shown in create form | ✓ | ✓ |
| Passed to `data_browser_create` | ✓ | ✓ |
| Patchable via `update` op | ✓ | ✗ (silently dropped) |
| Shown in edit form | ✓ | ✗ |

The schema the node returns includes `supports_create`, so the app knows whether to show the **+** button:

```json
{
  "ok": true,
  "mode": "enabled",
  "supports_create": true,
  "fields": [
    { "name": "text", "type": "string", "editable": true, "create_only": false },
    { "name": "scope", "type": "enum", "editable": false, "create_only": true,
      "enum_values": ["personal", "household"] }
  ]
}
```

Creating records needs `jarvis-command-sdk` 0.4.1 or later.

## On the Python node

The node's built-in commands can use the repositories under `JarvisStorage` directly. They are node internals (in `jarvis-node-setup`), not available on a computer; packages use `JarvisStorage`.

`repositories/command_data_repository.py`, `CommandDataRepository(session)`:

| Method | Does |
|--------|------|
| `save(command_name, data_key, data, expires_at=None)` | Upsert; `data` is a `dict`, JSON-encoded for you |
| `get(command_name, data_key, include_expired=False)` | The `dict`, or `None` (expired records hidden unless `include_expired=True`) |
| `get_all(command_name, include_expired=False)` | `dict`s with `_data_key` and `_expires_at` |
| `delete(command_name, data_key)`, `delete_all(command_name)`, `delete_expired()` | Delete |

```python
from db import SessionLocal
from repositories.command_data_repository import CommandDataRepository

with SessionLocal() as session:
    repo = CommandDataRepository(session)
    repo.save("my_command", "last_result", {"value": 42})
    result = repo.get("my_command", "last_result")
```

Rows are `CommandData` (`command_name`, `data_key`, `data` as JSON text, `expires_at`, `created_at`, `updated_at`), unique on `(command_name, data_key)`.

Other node repositories:

- `ChunkedCommandResponseRepository`: long responses stored by session (`create`, `get_by_session_id`, `update_content`, `delete_by_session_id`, `cleanup_old_sessions`). The voice pipeline uses it.
- `CommandRegistryRepository`: which commands are enabled (`get_all()`, `set_enabled(name, enabled)`, `ensure_registered(names)`; new commands default to enabled).
- `CommandAuth` (`models/command_auth.py`): sign-in status **per provider** (`provider`, `needs_auth`, `auth_error`, `last_checked_at`, `last_authed_at`), shared by every command that uses that provider. The settings screen reads it to show "authentication required".
