# Settings Client

The settings client library provides `SettingsService`, used by services to store and retrieve runtime configuration that can be changed without restarting. Values live in PostgreSQL and are cached locally with a configurable TTL.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-settings-client` |
| **Source** | `jarvis-settings-client/` |
| **Backend** | Per-service PostgreSQL table |

## Usage

Each service constructs a `SettingsService` with its setting definitions and a database session factory:

```python
from jarvis_settings_client import SettingsService, SettingDefinition

DEFINITIONS = [
    SettingDefinition(
        key="ocr.backend",
        category="ocr",
        value_type="string",
        default="tesseract",
        description="Active OCR backend",
        options=["tesseract", "easyocr", "paddleocr", "rapidocr"],
    ),
    SettingDefinition(
        key="feature.async_processing",
        category="feature",
        value_type="bool",
        default=False,
        description="Enable async OCR job queue",
    ),
]

settings = SettingsService(
    definitions=DEFINITIONS,
    get_db_session=lambda: db_session_factory(),
    cache_ttl_seconds=60,   # optional, default 60
)

# Read a value (typed helpers available)
backend = settings.get("ocr.backend")                   # returns str
enabled = settings.get_bool("feature.async_processing") # returns bool
timeout = settings.get_int("ocr.timeout", default=30)   # returns int

# Write a value
settings.set("ocr.backend", "easyocr")

# List all settings
all_settings = settings.list_all()
categories   = settings.list_categories()
```

## SettingDefinition Fields

| Field | Required | Description |
|-------|----------|-------------|
| `key` | Yes | Dotted key (e.g. `ocr.backend`) |
| `category` | Yes | Group name for `list_categories()` |
| `value_type` | Yes | `string`, `int`, `float`, `bool`, or `json` |
| `default` | Yes | Default value (used when no DB row exists) |
| `description` | Yes | Human-readable description shown in the admin UI |
| `env_fallback` | No | Environment variable to read if no DB row exists |
| `options` | No | Allowed values (validated on `set()`) |
| `requires_reload` | No | Whether changing this setting requires a service restart |
| `is_secret` | No | Mask the value in API responses |

## Typed Getters

| Method | Returns |
|--------|---------|
| `get(key, default=None)` | Raw value, type-coerced from DB |
| `get_str(key, default=None)` | `str` |
| `get_int(key, default=None)` | `int` |
| `get_float(key, default=None)` | `float` |
| `get_bool(key, default=None)` | `bool` |

## Multi-Tenant Scoping

Settings can be scoped to a household, node, or user by passing scope parameters. Lookups fall back from the most specific scope to the global value:

```python
# Get a setting for a specific household (falls back to global if not set)
backend = settings.get("ocr.backend", household_id="hh-123")

# Write a setting scoped to a node
settings.set("tts.provider", "piper", node_id="node-456")
```

## Environment Variable Fallback

If a setting has `env_fallback` defined and no DB row exists, the environment variable is read instead. Use `sync_from_env()` to migrate existing env-based config into the DB on first run:

```python
settings.sync_from_env()
```

## FastAPI Router

`create_settings_router()` adds standard CRUD endpoints (`GET /`, `PUT /{key}`) to a FastAPI app:

```python
from jarvis_settings_client import create_settings_router, create_combined_auth, create_superuser_auth

router = create_settings_router(
    service=settings,
    auth_dependency=create_combined_auth(auth_url),
    write_auth_dependency=create_superuser_auth(auth_url),
)
app.include_router(router, prefix="/settings")
```

## Caching

Values are cached in memory for `cache_ttl_seconds` (default 60 s). The cache is invalidated on any `set()` call. No restart is required for most setting changes — services poll the cache and pick up new values within one TTL cycle.

## Consumers

- **jarvis-ocr-service** — backend selection
- **jarvis-tts** — provider and voice selection
- **jarvis-command-center** — prompt provider and feature flags
- **jarvis-llm-proxy-api** — model selection and inference config
- **jarvis-whisper-api** — transcription settings
