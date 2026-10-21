# Settings Snapshots

The mobile app shows each node's settings (API keys, options, sign-ins) on its settings screens. The node builds that list itself, from what its commands, agents, device protocols and device managers declare, and the household edits the values from the app. A package never talks to this system directly.

## For Command Authors

The settings screen comes from your `required_secrets` declarations:

1. Declare each setting as a `JarvisSecret` with a `scope`, `value_type`, `is_sensitive` and `friendly_name`.
2. When the app opens the node's settings, the node lists every declared secret: its key, description, scope, type, friendly name and whether a value is set.
3. The app renders a field for each one.
4. What the user enters goes back to the node and is stored in its secret store, where `JarvisStorage(...).get_secret(key)` reads it.

```python
from jarvis_command_sdk import JarvisSecret

required_secrets = [
    JarvisSecret("OPENWEATHER_API_KEY", "OpenWeather API key", "integration", "string",
                 friendly_name="API key"),
    JarvisSecret("OPENWEATHER_UNITS", "imperial or metric", "integration", "string",
                 is_sensitive=False, friendly_name="Units", enum_values=["imperial", "metric"]),
]
```

How each declaration shows up in the app:

| Declaration | Field |
|-------------|-------|
| `is_sensitive=True` (the default) | Masked: the user can enter a new value but never sees the current one |
| `is_sensitive=False` | Plain text showing the current value |
| `value_type="bool"` | Toggle |
| `value_type="int"` | Number |
| `enum_values=[...]` | A picker |
| `value_type="user"` | A household-member picker; the value is that member's user id |
| `scope="user"` | Each household member sets their own value |

The scope is `"integration"` (one value for the household) or `"user"` (one per member); anything else raises `ValueError`. Commands with an OAuth `authentication` config also get a sign-in prompt. See [Secrets Deep Dive](../../commands/secrets.md) for every `JarvisSecret` option.

## How it works

For the curious; none of this is a package API.

1. The app asks the server for a node's settings, and the server asks the node over MQTT.
2. The node builds the snapshot (`build_snapshot()` in `services/settings_snapshot_service.py` on the Python node): every command, device family and device manager with its secrets metadata, enabled state and sign-in status, plus the node's hardware.
3. It encrypts the snapshot with **K2**, a key only the node and the household's phones hold (AES-256-GCM), and uploads it with `PUT /api/v0/nodes/{node_id}/settings/requests/{request_id}/snapshot`.
4. The app downloads it, decrypts it with K2 and renders the screens.

Changes go the other way through the same channel: the app encrypts the new values with K2, the server relays them, and the node decrypts them and stores them. The server only ever sees ciphertext. K2 reaches the node when it is [provisioned](../../clients/provisioning.md).
