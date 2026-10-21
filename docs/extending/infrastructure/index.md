# Infrastructure Services

A package reaches the device's storage, secrets and the server through the [Command SDK](../../libraries/command-sdk.md). The SDK's helpers work wherever the package runs: the device registers the backends behind them at startup. Import them from `jarvis_command_sdk`.

## For packages: the SDK

| You need to... | Use |
|----------------|-----|
| Ask the LLM for a text reply | [`llm_chat_text(prompt)`](jcc-client.md) |
| POST to a server route as the node | [`cc_post(path, json)`](jcc-client.md#call-the-server) |
| Read an API key or other setting | [`JarvisStorage(name).get_secret(key)`](secrets.md) |
| Cache data between runs, with optional expiry | [`JarvisStorage(name).save(key, data, expires_at)`](datastore.md#jarvisstorage-sdk-persistence-facade) |
| Check if a pidfile-tracked daemon is alive | [`process_alive(pid, expected_comm=...)`](process.md) |
| Expose settings to the mobile app | Declare them in [`required_secrets`](settings.md#for-command-authors) |

```python
from jarvis_command_sdk import JarvisStorage, llm_chat_text

storage = JarvisStorage("my_command")
api_key = storage.get_secret("MY_API_KEY")  # integration scope by default
storage.save("last_run", {"ok": True})
reply = llm_chat_text("Say hello in French.")  # None when there is no LLM
```

A computer's desktop agent has only the SDK, and it registers no LLM or server backend: there `llm_chat_text` and `cc_post` return `None`. See [Where your code runs](../where-code-runs.md).

## On the Python node only

The Python Pi node (`jarvis-node-setup`) has its own modules under the SDK. Its built-in commands use them, and they are what the SDK's backends call on a Pi. A package should not import them: they don't exist on a computer, and they change with the node.

| Module | Purpose |
|--------|---------|
| `services/secret_service.py` | Secrets in the node's encrypted database; what `JarvisStorage.get_secret` reads on a Pi |
| `repositories/command_data_repository.py` | Per-command key-value data with expiry; what `JarvisStorage.save` writes on a Pi |
| `clients/jarvis_command_center_client.py` | The node's server client (voice pipeline, conversations); see [Command Center Client](jcc-client.md#the-nodes-own-client) |
| `services/settings_snapshot_service.py` | Encrypted settings snapshots for the mobile app; see [Settings Snapshots](settings.md) |
| `repositories/command_registry_repository.py` | Which commands are enabled |

## Encrypted storage

The node keeps secrets, command data and the command registry in an **encrypted SQLite database** (SQLCipher, through the `sqlcipher3` library). The key is at `~/.jarvis/db.key` (or `$JARVIS_SECRET_DIRECTORY/db.key`) and is created the first time the database is opened. The database file is `./jarvis_node.db` in the node's working directory, or `$JARVIS_NODE_DB`.

Without the key file the data is unreadable, even with the SD card in hand.
