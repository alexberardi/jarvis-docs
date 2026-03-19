# Secret Service

The secret service provides encrypted key-value storage for API keys, tokens, and configuration values. All secrets are stored in the node's encrypted SQLite database (pysqlcipher3, AES-256-CBC with 256K KDF iterations).

**Module:** `services/secret_service.py`

!!! tip "Declaring secrets vs. reading secrets"
    This page covers the **runtime API** for reading and writing secrets. For how to declare what secrets your command needs, see [Secrets Deep Dive](../../commands/secrets.md).

## High-Level API

The secret service exposes module-level functions that handle database sessions internally. Each call opens and closes its own session, making them safe to call from any thread.

### Reading Secrets

```python
from services.secret_service import get_secret_value, get_secret_value_int

# Read a string secret
api_key = get_secret_value("OPENWEATHER_API_KEY", "integration")
# Returns the value as a string, or None if not found

# Read an integer secret with type conversion
port = get_secret_value_int("CUSTOM_PORT", "node")
# Returns the value as an int, or None if not found/not parseable
```

### Writing Secrets

```python
from services.secret_service import set_secret

# Store a string value
set_secret("MY_API_KEY", "sk-abc123...", "integration", "string")

# Store an integer
set_secret("CUSTOM_PORT", "8080", "node", "int")

# Store a boolean
set_secret("FEATURE_ENABLED", "true", "integration", "bool")
```

### Deleting Secrets

```python
from services.secret_service import delete_secret

delete_secret("OLD_KEY", "integration")
```

### Checking Existence

```python
from services.secret_service import ensure_secret_exists

# Creates the secret row if it doesn't exist (with empty value)
# Does NOT overwrite existing values
ensure_secret_exists("MY_KEY", "integration", "string")
```

### Listing All Secrets

```python
from services.secret_service import get_all_secrets

# Get all secrets in a scope
secrets = get_all_secrets("integration")
for secret in secrets:
    print(f"{secret.key} = {secret.value} (type: {secret.value_type})")
```

### Bulk Seeding

Used by `install_command.py` to create empty secret rows for all commands:

```python
from services.secret_service import seed_command_secrets

# Discovers required_secrets from a command and ensures rows exist
seed_command_secrets(command.required_secrets)
```

This is idempotent --- existing values are never overwritten.

## Scopes

Secrets have one of two scopes that determine how they are shared across nodes in a household.

### `"integration"` --- Shared Across All Nodes

Use for configuration that applies to the entire household. When the mobile app pushes a new value for an integration-scoped secret, it is synchronized to all nodes.

- API keys (OpenWeather, financial data, sports)
- OAuth tokens (Gmail, Spotify)
- Service URLs (Home Assistant, Music Assistant)
- Shared preferences (unit system, language)

```python
api_key = get_secret_value("OPENWEATHER_API_KEY", "integration")
```

### `"node"` --- Per-Node

Use for configuration that varies by physical location or hardware:

- Default location (kitchen node in Denver, office node in NYC)
- Audio device settings
- Room-specific preferences

```python
location = get_secret_value("OPENWEATHER_LOCATION", "node")
```

## Value Types

| Type | Storage | Use Case |
|------|---------|----------|
| `"string"` | Text as-is | API keys, URLs, tokens |
| `"int"` | Text, converted on read via `get_secret_value_int()` | Port numbers, thresholds |
| `"bool"` | `"true"` / `"false"` text | Feature flags |

All values are stored as strings internally. The `value_type` field is metadata that tells the mobile settings UI how to render the input (text field vs. number stepper vs. toggle).

## The Secret Model

```python
class Secret:
    key: str          # Unique identifier (e.g., "OPENWEATHER_API_KEY")
    value: str        # The stored value (always a string)
    scope: str        # "integration" or "node"
    value_type: str   # "string", "int", or "bool"
```

The uniqueness constraint is on `(key, scope)` --- the same key name can exist in both scopes with different values.

## Installation Flow

The `install_command.py` script handles secret seeding for all commands:

```bash
# Seed secrets for all discovered commands
python scripts/install_command.py --all

# Seed secrets for a single command
python scripts/install_command.py get_weather

# List commands and their required secrets
python scripts/install_command.py --list
```

Under the hood, for each command:

1. The script instantiates the command class
2. Reads `all_possible_secrets` (falls back to `required_secrets`)
3. Calls `seed_command_secrets()` which runs `ensure_secret_exists()` for each secret
4. Existing values are never overwritten --- safe to re-run at any time

## Thread Safety

Each function in the secret service opens its own database session and closes it when done. There is no shared session state. This means you can safely call `get_secret_value()` from any thread, including background timers and the voice pipeline thread.

```python
# Safe to call from any thread --- no shared state
def run(self, request_info, **kwargs) -> CommandResponse:
    api_key = get_secret_value("MY_KEY", "integration")  # Thread-safe
    # ...
```

## Encrypted Backend

The underlying SQLite database is encrypted with pysqlcipher3:

- **Cipher:** AES-256-CBC
- **KDF iterations:** 256,000
- **Key file:** `~/.jarvis/db.key`
- **Database file:** `~/.jarvis/jarvis.db`

The key file is generated during node provisioning and is specific to each node. The database is unreadable without the key.

## Typical Usage in a Command

```python
from services.secret_service import get_secret_value
from core.ijarvis_command import IJarvisCommand
from core.jarvis_secret import JarvisSecret
from models.command_response import CommandResponse

class GetStockPrice(IJarvisCommand):
    @property
    def name(self) -> str:
        return "get_stock_price"

    @property
    def required_secrets(self) -> list:
        return [
            JarvisSecret(
                "FINANCE_API_KEY", "Financial data API key",
                "integration", "string",
                friendly_name="API Key"
            ),
            JarvisSecret(
                "DEFAULT_CURRENCY", "Default display currency",
                "integration", "string",
                required=False, is_sensitive=False,
                friendly_name="Currency"
            ),
        ]

    def run(self, request_info, **kwargs) -> CommandResponse:
        # Required secret --- guaranteed present by _validate_secrets()
        api_key = get_secret_value("FINANCE_API_KEY", "integration")

        # Optional secret --- check manually
        currency = get_secret_value("DEFAULT_CURRENCY", "integration") or "USD"

        symbol = kwargs.get("symbol", "AAPL")
        price = self._fetch_price(api_key, symbol, currency)

        return CommandResponse.text_response(
            text=f"{symbol} is trading at {price} {currency}"
        )
```
