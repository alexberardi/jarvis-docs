# Infrastructure Services

Commands, agents, and other extensions have access to a rich set of infrastructure services on the node. These utilities handle everything from HTTP communication with the command center to encrypted secret storage and persistent data.

This section covers the developer-facing APIs that your plugins can use at runtime.

## Available Services

| Service | Module | Purpose |
|---------|--------|---------|
| [Command Center Client](jcc-client.md) | `clients/jarvis_command_center_client.py` | HTTP client for CC (voice commands, LLM chat, training, conversations) |
| [Secret Service](secrets.md) | `services/secret_service.py` | Read/write secrets from encrypted SQLite |
| [Command Data Store](datastore.md) | `repositories/command_data_repository.py` | Generic key-value persistence with TTL |
| [Settings Snapshots](settings.md) | `services/settings_snapshot_service.py` | Build encrypted settings for mobile sync |
| Command Registry | `repositories/command_registry_repository.py` | Enable/disable commands |

## Encrypted Storage

All data is stored in an **encrypted SQLite database** using pysqlcipher3 (AES-256-CBC, 256K KDF iterations). The encryption key lives at `~/.jarvis/db.key` and is generated automatically during node provisioning.

This means secrets, command data, and registry state are encrypted at rest. Even if someone gains physical access to the Pi Zero's SD card, the data is unreadable without the key file.

## Common Access Pattern

Most infrastructure services are accessed through simple module-level functions or repository classes that take a database session:

```python
# Module-level functions (secret service)
from services.secret_service import get_secret_value, set_secret

api_key = get_secret_value("MY_API_KEY", "integration")

# Repository classes (data store, registry)
from db import SessionLocal
from repositories.command_data_repository import CommandDataRepository

db = SessionLocal()
repo = CommandDataRepository(db)
entry = repo.get("my_command", "cache_key")
db.close()

# Singleton client (command center)
from clients.jarvis_command_center_client import JarvisCommandCenterClient

client = JarvisCommandCenterClient()
result = client.chat_text("What time is it in Tokyo?")
```

## When to Use What

| You need to... | Use |
|----------------|-----|
| Call the LLM for structured parsing | [Command Center Client](jcc-client.md) --- `chat()` or `lightweight_chat()` |
| Read an API key or config value | [Secret Service](secrets.md) --- `get_secret_value()` |
| Cache data between command invocations | [Command Data Store](datastore.md) --- `CommandDataRepository` |
| Store temporary results with auto-expiry | [Command Data Store](datastore.md) --- `save()` with `expires_at` |
| Expose settings to the mobile app | [Settings Snapshots](settings.md) --- automatic via `required_secrets` |
| Check if a command is enabled | Command Registry --- `CommandRegistryRepository.get_all()` |
