# Command Data Store

The `CommandDataRepository` provides generic key-value persistence for commands that need to store state between invocations. Use it for caching API responses, tracking timers, persisting shopping lists, or any data that should survive a node restart.

**Module:** `repositories/command_data_repository.py`

## Quick Start

```python
from db import SessionLocal
from repositories.command_data_repository import CommandDataRepository
import json

db = SessionLocal()
repo = CommandDataRepository(db)

# Save
repo.save(
    command_name="my_command",
    data_key="last_result",
    data=json.dumps({"value": 42})
)

# Read
entry = repo.get("my_command", "last_result")
if entry:
    result = json.loads(entry.data)

db.close()
```

## API Reference

### `save(command_name, data_key, data, expires_at=None)`

Store or update a key-value entry. If an entry with the same `(command_name, data_key)` already exists, it is overwritten.

```python
from datetime import datetime, timedelta

# Simple save
repo.save(
    command_name="get_weather",
    data_key="cache:Miami",
    data=json.dumps({"temp": 75, "condition": "sunny"})
)

# Save with TTL (auto-expires in 1 hour)
repo.save(
    command_name="get_weather",
    data_key="cache:Miami",
    data=json.dumps({"temp": 75, "condition": "sunny"}),
    expires_at=datetime.utcnow() + timedelta(hours=1)
)
```

### `get(command_name, data_key) -> Optional[CommandData]`

Retrieve a single entry. Returns `None` if the key does not exist.

!!! warning
    `get()` does not check `expires_at`. Expired entries are still returned until explicitly cleaned up with `delete_expired()`. Check the expiration yourself if it matters for your use case.

```python
entry = repo.get("get_weather", "cache:Miami")
if entry:
    data = json.loads(entry.data)
    if entry.expires_at and entry.expires_at < datetime.utcnow():
        # Entry has expired, treat as cache miss
        data = None
```

### `get_all(command_name) -> list[CommandData]`

Retrieve all entries for a given command.

```python
entries = repo.get_all("shopping_list")
for entry in entries:
    print(f"{entry.data_key}: {entry.data}")
```

### `delete(command_name, data_key)`

Delete a single entry.

```python
repo.delete("get_weather", "cache:Miami")
```

### `delete_all(command_name)`

Delete all entries for a command.

```python
repo.delete_all("my_command")
```

### `delete_expired()`

Remove all entries across all commands where `expires_at` is in the past. Call this periodically (e.g., from a background timer or at node startup) to clean up stale data.

```python
repo.delete_expired()
```

## The CommandData Model

```python
class CommandData:
    command_name: str      # The command this data belongs to
    data_key: str          # Unique key within the command
    data: str              # The stored value (text/JSON)
    created_at: datetime   # When the entry was first created
    updated_at: datetime   # When the entry was last modified
    expires_at: datetime | None  # Optional TTL timestamp
```

**Uniqueness constraint:** `(command_name, data_key)` --- each command can have many keys, but each key is unique per command.

## Use Cases

### Caching API Responses

Reduce API calls by caching results with a TTL:

```python
import json
from datetime import datetime, timedelta

CACHE_TTL = timedelta(minutes=30)

def _get_weather_cached(self, repo, city: str) -> dict | None:
    entry = repo.get("get_weather", f"cache:{city}")
    if entry and entry.expires_at and entry.expires_at > datetime.utcnow():
        return json.loads(entry.data)
    return None

def _cache_weather(self, repo, city: str, data: dict):
    repo.save(
        command_name="get_weather",
        data_key=f"cache:{city}",
        data=json.dumps(data),
        expires_at=datetime.utcnow() + CACHE_TTL
    )
```

### Persistent Lists

Store user data that persists across invocations:

```python
def add_to_shopping_list(self, repo, item: str):
    existing = repo.get("shopping_list", "items")
    items = json.loads(existing.data) if existing else []
    items.append(item)
    repo.save(
        command_name="shopping_list",
        data_key="items",
        data=json.dumps(items)
    )

def get_shopping_list(self, repo) -> list[str]:
    entry = repo.get("shopping_list", "items")
    return json.loads(entry.data) if entry else []
```

### Timer State

Track active timers that survive node restarts:

```python
from datetime import datetime

def set_timer(self, repo, label: str, end_time: datetime):
    repo.save(
        command_name="timer",
        data_key=f"active:{label}",
        data=json.dumps({
            "label": label,
            "end_time": end_time.isoformat()
        }),
        expires_at=end_time  # Auto-cleanup after timer fires
    )

def get_active_timers(self, repo) -> list[dict]:
    entries = repo.get_all("timer")
    now = datetime.utcnow()
    return [
        json.loads(e.data)
        for e in entries
        if e.data_key.startswith("active:")
        and (e.expires_at is None or e.expires_at > now)
    ]
```

## Chunked Command Response Repository

For commands that produce large streaming responses (e.g., deep research), the `ChunkedCommandResponseRepository` stores response chunks keyed by session ID.

```python
from repositories.chunked_command_response_repository import ChunkedCommandResponseRepository

db = SessionLocal()
repo = ChunkedCommandResponseRepository(db)

# Store chunks as they arrive
repo.append_chunk(session_id="sess-123", chunk="First part of the response...")
repo.append_chunk(session_id="sess-123", chunk="Second part...")

# Retrieve all chunks for a session
chunks = repo.get_chunks(session_id="sess-123")
full_response = "".join(chunks)

# Clean up after delivery
repo.delete_session(session_id="sess-123")

db.close()
```

This is used internally by the voice pipeline for commands that stream results over multiple turns.

## Command Registry Repository

The `CommandRegistryRepository` tracks which commands are enabled or disabled. It is used by `CommandDiscoveryService` to filter the active command set.

```python
from db import SessionLocal
from repositories.command_registry_repository import CommandRegistryRepository

db = SessionLocal()
repo = CommandRegistryRepository(db)

# Get enabled/disabled state for all commands
registry = repo.get_all()
# registry == {"get_weather": True, "calculate": True, "my_command": False}

# Enable or disable a command
repo.set_enabled("my_command", True)

# Ensure all discovered commands have a registry entry
# New commands default to enabled; existing entries are not changed
repo.ensure_registered(["get_weather", "calculate", "my_command"])

db.close()
```

## Command Auth Service

The `command_auth_service` module and `CommandAuth` model track OAuth authentication status for commands that use external providers (e.g., Gmail, Spotify).

```python
from models.command_auth import CommandAuth
```

The `CommandAuth` model:

```python
class CommandAuth:
    command_name: str     # The command (e.g., "send_email")
    provider: str         # Auth provider (e.g., "gmail")
    needs_auth: bool      # Whether OAuth flow needs to be completed
    auth_error: str | None  # Error message if auth failed
```

The settings snapshot system reads `CommandAuth` entries to show an "authentication required" badge in the mobile app, prompting the user to complete the OAuth flow.

## Session Management

The data store requires a SQLAlchemy session from `SessionLocal()`. Always close the session when you are done:

```python
from db import SessionLocal
from repositories.command_data_repository import CommandDataRepository

db = SessionLocal()
try:
    repo = CommandDataRepository(db)
    repo.save("my_command", "key", "value")
finally:
    db.close()
```

In command `run()` methods, you typically create a session at the start and close it at the end. If your command is short-lived and only makes one or two data store calls, the overhead is minimal.
