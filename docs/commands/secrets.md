# Secrets Deep Dive

Secrets store configuration that commands need at runtime -- API keys, tokens, user preferences, and service URLs. They are managed through an encrypted SQLite database on the node and synchronized with the mobile app via settings snapshots.

## JarvisSecret Constructor

```python
JarvisSecret(
    key: str,                       # Unique identifier (e.g., "OPENWEATHER_API_KEY")
    description: str,               # Human-readable description
    scope: str,                     # "integration" or "node"
    value_type: str,                # "string", "int", or "bool"
    required: bool = True,          # Whether command fails without it
    is_sensitive: bool = True,      # Whether value appears in settings snapshots
    friendly_name: str | None = None,  # Display name for mobile UI
)
```

## Scopes

### `"integration"` -- Shared Across All Nodes

Use for config that applies to the entire household:

- API keys (OpenWeather, financial data, etc.)
- OAuth tokens (Gmail, Spotify)
- Service URLs (Home Assistant, Music Assistant)
- Shared preferences (unit system, language)

```python
JarvisSecret(
    "OPENWEATHER_API_KEY",
    "Open Weather API Key",
    "integration",       # All nodes in this household use the same key
    "string",
)
```

### `"node"` -- Per-Node

Use for config that varies by physical location or device:

- Default location (kitchen node in Denver, office node in NYC)
- Audio device settings
- Room-specific preferences

```python
JarvisSecret(
    "OPENWEATHER_LOCATION",
    "Default weather location (city,state,country)",
    "node",              # Each node can have a different default location
    "string",
    is_sensitive=False,
    friendly_name="Default Location",
)
```

**Invalid scope values raise `ValueError` at construction time.**

## Value Types

| Type | Description | Example |
|------|-------------|---------|
| `"string"` | Text values | API keys, URLs, tokens |
| `"int"` | Integer values | Port numbers, thresholds |
| `"bool"` | Boolean values | Feature flags |

**Invalid value types raise `ValueError` at construction time.**

All values are stored as strings internally. Use appropriate conversion in your `run()` method:

```python
port = int(get_secret_value("MY_SERVICE_PORT", "integration") or "8080")
enabled = get_secret_value("FEATURE_FLAG", "node") == "true"
```

## Sensitivity

### `is_sensitive=True` (Default)

Sensitive secrets are **not included** in settings snapshots sent to the mobile app. The mobile app shows a masked placeholder and allows users to enter a new value, but never sees the current value.

Use for: API keys, passwords, tokens, client secrets.

```python
JarvisSecret(
    "FINANCE_API_KEY", "API key", "integration", "string",
    is_sensitive=True,  # Default -- value never leaves the node
)
```

### `is_sensitive=False`

Non-sensitive values **are included** in settings snapshots. The mobile app can display and edit the current value.

Use for: URLs, locations, unit preferences, display names.

```python
JarvisSecret(
    "OPENWEATHER_UNITS", "Imperial, Metric, or Kelvin", "integration", "string",
    is_sensitive=False,  # Mobile app shows current value
    friendly_name="Units",
)
```

## Friendly Names

The `friendly_name` is what users see in the mobile settings UI instead of the raw key:

```python
JarvisSecret("OPENWEATHER_API_KEY", ..., friendly_name="API Key")
JarvisSecret("OPENWEATHER_UNITS", ..., friendly_name="Units")
JarvisSecret("OPENWEATHER_LOCATION", ..., friendly_name="Default Location")
```

In the mobile app, under the "OpenWeather" service group, users see:

```
OpenWeather
  API Key          ••••••••
  Units            imperial
  Default Location Miami,FL,US
```

If `friendly_name` is `None`, the mobile app falls back to displaying the raw key name.

## Installation Flow

### `install_command.py`

The install script discovers all command classes, runs database migrations, and seeds the secrets table:

```bash
# List all commands and their secrets
python scripts/install_command.py --list

# Install all commands
python scripts/install_command.py --all

# Install a single command
python scripts/install_command.py get_weather
```

The install script:

1. Finds the command class
2. Reads `all_possible_secrets` (falls back to `required_secrets`)
3. Creates empty-value rows in the secrets database for each secret
4. **Never overwrites existing values** -- safe to re-run

### `all_possible_secrets`

When `required_secrets` is config-dependent, override `all_possible_secrets` to declare every secret the command could ever need:

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    # Returns different secrets based on EMAIL_PROVIDER setting
    provider = get_email_provider()
    if provider == "imap":
        return [imap_username, imap_password]
    else:
        return [gmail_client_id]

@property
def all_possible_secrets(self) -> List[IJarvisSecret]:
    # Always returns ALL variants -- used by install_command.py
    return [
        email_provider,
        gmail_client_id, gmail_access_token, gmail_refresh_token,
        imap_host, imap_port, imap_username, imap_password,
        smtp_host, smtp_port,
    ]
```

This ensures `install_command.py` seeds all possible secret rows, regardless of the current configuration.

## Setting Secret Values

### Mobile App (Settings Sync)

The primary way users set secrets:

1. Open the mobile app
2. Navigate to Nodes tab, tap a node
3. Find the command's service group
4. Enter values in the settings form
5. The mobile app pushes the encrypted settings to the node via the command center

### `set_secret.py` (Dev/CLI)

For development or headless setup:

```bash
python utils/set_secret.py OPENWEATHER_API_KEY "your-key-here" integration
python utils/set_secret.py OPENWEATHER_LOCATION "Miami,FL,US" node
```

### Programmatically

In `store_auth_values()` or `init_data()`:

```python
from services.secret_service import set_secret

set_secret("GMAIL_ACCESS_TOKEN", token_value, "integration")
```

## Reading Secrets at Runtime

Use `get_secret_value()` in your `run()` method:

```python
from services.secret_service import get_secret_value

def run(self, request_info, **kwargs) -> CommandResponse:
    api_key = get_secret_value("OPENWEATHER_API_KEY", "integration")
    if not api_key:
        return CommandResponse.error_response(
            error_details="OpenWeather API key is not configured. Set it in your settings.",
        )
    location = get_secret_value("OPENWEATHER_LOCATION", "node")
    # ...
```

**Important:** Even though `_validate_secrets()` runs before `run()`, the check only verifies that `required=True` secrets are present. For optional secrets, you must check manually.

## Secret Validation in the Pipeline

The `execute()` method on `JarvisCommandBase` calls `_validate_secrets()` before your `run()`:

```python
def _validate_secrets(self):
    missing = []
    for secret in self.required_secrets:
        if secret.required and not get_secret_value(secret.key, secret.scope):
            missing.append(secret.key)
    if missing:
        raise MissingSecretsError(missing)
```

If any required secret is missing, a `MissingSecretsError` is raised. The command center catches this and returns an appropriate error message to the user.

## Patterns

### API Key + Non-Sensitive Config

The most common pattern -- one sensitive key, one or more non-sensitive preferences:

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    return [
        JarvisSecret("MY_API_KEY", "API key", "integration", "string",
                      friendly_name="API Key"),
        JarvisSecret("MY_DEFAULT_REGION", "Default region", "integration", "string",
                      is_sensitive=False, friendly_name="Region"),
    ]
```

### Service URL + Token

For self-hosted services where the URL varies by installation:

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    return [
        JarvisSecret("SERVICE_URL", "Service URL (e.g., http://192.168.1.50:8080)",
                      "integration", "string", is_sensitive=False, friendly_name="URL"),
        JarvisSecret("SERVICE_TOKEN", "Auth token",
                      "integration", "string", friendly_name="Token"),
    ]
```

### Optional Secrets with Fallbacks

For secrets with runtime fallbacks:

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    return [
        JarvisSecret("WEATHER_API_KEY", "Required API key",
                      "integration", "string", required=True),
        JarvisSecret("WEATHER_LOCATION", "Optional default location",
                      "node", "string", required=False, is_sensitive=False),
    ]

def run(self, request_info, **kwargs):
    city = kwargs.get("city")
    if not city:
        city = get_secret_value("WEATHER_LOCATION", "node")
    if not city:
        city = self._detect_location_from_ip()
    # ...
```

### Multiple Providers (Config-Variant)

When the same command supports multiple backends:

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    provider = get_email_provider()  # Reads EMAIL_PROVIDER secret
    base = [
        JarvisSecret("EMAIL_PROVIDER", "gmail or imap", "integration", "string",
                      required=False, is_sensitive=False),
    ]
    if provider == "imap":
        base.extend([...imap secrets...])
    else:
        base.extend([...gmail secrets...])
    return base

@property
def all_possible_secrets(self) -> List[IJarvisSecret]:
    return [...all gmail secrets...] + [...all imap secrets...]
```
