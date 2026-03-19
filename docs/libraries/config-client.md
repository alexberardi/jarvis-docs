# Config Client

The config client library provides `ConfigClient`, used by services to discover URLs of other services at runtime via the [Config Service](../services/config-service.md).

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-config-client` |
| **Source** | `jarvis-config-client/` |
| **Backend** | jarvis-config-service (port 7700) |

## Usage

```python
from jarvis_config_client import ConfigClient

config = ConfigClient(config_url="http://jarvis-config-service:7700")

# Get a specific service URL
auth_url = config.get_service_url("jarvis-auth")
# => "http://jarvis-auth:7701"

# Get all services
services = config.get_all_services()
# => {"jarvis-auth": "http://jarvis-auth:7701", ...}
```

## Configuration

| Parameter | Env Variable | Description |
|-----------|-------------|-------------|
| `config_url` | `JARVIS_CONFIG_URL` | URL of the config service |

## Caching

Service URLs are cached locally and refreshed periodically. This means services can tolerate brief config service outages after initial startup.

## URL Styles

The config service supports two URL styles controlled by `JARVIS_CONFIG_URL_STYLE`:

- **Default** -- returns container names (e.g., `http://jarvis-auth:7701`), used by Docker services on the shared network
- **`dockerized`** -- returns `host.docker.internal` URLs, used when Docker containers need to reach locally-running services (e.g., LLM proxy on macOS)
