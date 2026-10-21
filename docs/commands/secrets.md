# Secrets Deep Dive

Secrets store configuration that commands need at runtime -- API keys, tokens, user preferences, and service URLs. They are managed through an encrypted SQLite database on each node and synchronized with the mobile app via settings snapshots. `JarvisSecret` and `JarvisStorage` are imported from `jarvis_command_sdk`.

## JarvisSecret Constructor

```python
JarvisSecret(
    key: str,                       # Unique identifier (e.g., "OPENWEATHER_API_KEY")
    description: str,               # Human-readable description
    scope: str,                     # "integration" or "user"
    value_type: str,                # "string", "int", "bool" or "user"
    required: bool = True,          # Whether command fails without it
    is_sensitive: bool = True,      # Whether value appears in settings snapshots
    friendly_name: str | None = None,  # Display name for mobile UI
    enum_values: list[str] | None = None,  # Allowed values (mobile shows a dropdown)
    presets: dict[str, dict[str, str]] | None = None,  # Values to fill in per enum choice
)
```

`enum_values` needs `value_type="string"`. `presets` needs `enum_values`: its keys are enum values, and choosing one in the app fills in the related secrets, e.g. the IMAP host and port for a mail provider:

```python
JarvisSecret(
    "EMAIL_PROVIDER", "Mail provider", "integration", "string",
    is_sensitive=False,
    enum_values=["gmail", "icloud"],
    presets={
        "icloud": {"IMAP_HOST": "imap.mail.me.com", "IMAP_PORT": "993"},
    },
)
```

## Scopes

### `"integration"` -- One Value per Node

Use for config that is the same for everyone who uses the node:

- API keys (OpenWeather, financial data, etc.)
- OAuth tokens (Gmail, Spotify)
- Service URLs (Home Assistant, Music Assistant)
- Shared preferences (unit system, language)

```python
JarvisSecret(
    "OPENWEATHER_API_KEY",
    "Open Weather API Key",
    "integration",       # Everyone on this node uses the same key
    "string",
)
```

Secrets live in each node's own encrypted database, so an `integration` value is set per node. To reuse it, the mobile app's node settings can copy a service's configured secrets to your other nodes (the target nodes need their encryption key imported first).

### `"user"` -- Per-User

Use for credentials or preferences that differ per household member:

- Personal email credentials (each family member has their own)
- Personal OAuth tokens
- Per-user preferences

```python
JarvisSecret(
    "EMAIL_ADDRESS",
    "Your email address",
    "user",              # Each household member has their own value
    "string",
    is_sensitive=False,
    friendly_name="Email Address",
)
```

**Invalid scope values raise `ValueError` at construction time.**

## Value Types

| Type | Description | Example |
|------|-------------|---------|
| `"string"` | Text values | API keys, URLs, tokens |
| `"int"` | Integer values | Port numbers, thresholds |
| `"bool"` | Boolean values | Feature flags |
| `"user"` | A household member (the app shows a member picker; the value is the member's user id as a string) | Who a background agent posts notifications to |

**Invalid value types raise `ValueError` at construction time.**

All values are stored as strings internally. Use appropriate conversion in your `run()` method:

```python
secrets = kwargs.get("secrets") or {}
port = int(secrets.get("MY_SERVICE_PORT") or "8080")
enabled = secrets.get("FEATURE_FLAG") == "true"
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
5. The mobile app pushes the encrypted settings to the node through your `jarvisd` server, and the node stores them

### `set_secret.py` (Dev/CLI)

For development or headless setup, from a shell in the node's directory (`/opt/jarvis-node` on an installed Pi):

```bash
python utils/set_secret.py set --key OPENWEATHER_API_KEY --value "your-key-here" --scope integration
python utils/set_secret.py set --key OPENWEATHER_LOCATION --value "Miami,FL,US" --scope integration
```

`--scope` defaults to `integration`; the other scope is `user`. The tool also has `get`, `delete` and `list` subcommands.

### Programmatically

In `store_auth_values()` or `init_data()`, use `JarvisStorage`:

```python
from jarvis_command_sdk import JarvisStorage

JarvisStorage("email").set_secret("GMAIL_ACCESS_TOKEN", token_value)  # scope "integration"
JarvisStorage("email", secret_scope="user").set_secret("EMAIL_ADDRESS", address)  # current user
```

A `"user"` scope resolves to the current user (the speaker, or the user who connected the account). If the host registered no storage backend, `get_secret()` returns `None` and `set_secret()` does nothing.

## Reading Secrets at Runtime

The node passes your secrets into `run()` as the `secrets` keyword: every secret in `required_secrets` (required or not) that has a value, read for the current user where the scope is `"user"`:

```python
def run(self, request_info, **kwargs) -> CommandResponse:
    secrets = kwargs.get("secrets") or {}
    api_key = secrets.get("OPENWEATHER_API_KEY")
    if not api_key:
        return CommandResponse.error_response(
            error_details="OpenWeather API key is not configured. Set it in your settings.",
        )
    location = secrets.get("OPENWEATHER_LOCATION")
    # ...
```

Anywhere else (or for a secret not in `required_secrets`), read it with `JarvisStorage`:

```python
from jarvis_command_sdk import JarvisStorage

location = JarvisStorage("get_weather").get_secret("OPENWEATHER_LOCATION")
```

**Important:** Even though the secret presence check runs before `run()`, it only verifies that `required=True` secrets are present. For optional secrets, you must check manually.

!!! note "`services.secret_service`"
    Older commands call `get_secret_value()` and `set_secret()` from `services.secret_service`. That module exists only inside the Python node, so such a command fails on a desktop agent. Use the `secrets` keyword or `JarvisStorage`.

## Secret Validation in the Pipeline

The `execute()` method on `IJarvisCommand` checks the host-supplied `secrets` dict before your `run()`:

```python
if secrets is not None:
    missing = [
        s.key for s in self.required_secrets
        if s.required and not secrets.get(s.key)
    ]
    if missing:
        raise MissingSecretsError(missing)
```

If any required secret is missing, a `MissingSecretsError` is raised and `run()` is never called. The node catches it like any exception from a tool and sends `jarvisd` a failed tool result with the message `Missing required secrets: <keys>`. The user hears the model's reply to that failure or, when the node falls back to its own message, "Sorry, that didn't work: Missing required secrets: ...". Nothing points the user to the settings, so a clear `friendly_name` and `setup_guide` help.

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
                      "integration", "string", required=False, is_sensitive=False),
    ]

def run(self, request_info, **kwargs):
    city = kwargs.get("city")
    if not city:
        city = (kwargs.get("secrets") or {}).get("WEATHER_LOCATION")
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
