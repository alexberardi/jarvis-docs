# Settings Client

The settings client library provides a read interface for runtime settings stored in the database. Services use it to check feature flags, backend preferences, and other configuration that can be changed without restarting.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-settings-client` |
| **Source** | `jarvis-settings-client/` |
| **Backend** | Settings stored in PostgreSQL (per-service) |

## Usage

```python
from jarvis_settings_client import SettingsClient

settings = SettingsClient(database_url="postgresql://...")

# Read a setting
backend = settings.get("ocr.backend", default="tesseract")

# Check a boolean flag
if settings.get_bool("feature.async_processing", default=False):
    process_async()
```

## Configuration

| Parameter | Env Variable | Description |
|-----------|-------------|-------------|
| `database_url` | `DATABASE_URL` | PostgreSQL connection string |

## Setting Keys

Settings use dotted key notation (e.g., `llm.interface`, `ocr.backend`). Each service defines its own namespace. Common patterns:

- `llm.interface` -- prompt provider selection
- `ocr.backend` -- OCR engine selection
- `feature.*` -- feature flags

## Consumers

- **jarvis-ocr-service** -- backend selection opt-in
- **jarvis-recipes-server** -- runtime configuration
- **jarvis-command-center** -- prompt provider and feature flags
