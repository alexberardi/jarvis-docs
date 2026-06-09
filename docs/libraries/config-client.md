# Config Client

The config client library provides service URL discovery via the [Config Service](../services/config-service.md). The recommended pattern is to call `init()` once at startup and then use module-level helper functions throughout the service.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-config-client` |
| **Source** | `jarvis-config-client/` |
| **Backend** | jarvis-config-service (port 7700) |

## Usage

```python
import jarvis_config_client as config

# Call once at startup
config.init(config_url="http://jarvis-config-service:7700")

# Resolve service URLs anywhere in your code
auth_url = config.get_service_url("jarvis-auth")
# => "http://jarvis-auth:7701"

# Short names also work
auth_url = config.get_service_url("auth")

# Get all registered services
services = config.get_all()
# => {"jarvis-auth": ServiceConfig(...), ...}

# Named convenience helpers (preferred)
auth_url   = config.get_auth_url()
logs_url   = config.get_logs_url()
ocr_url    = config.get_ocr_url()
# ...and so on for each core service
```

Calling `init()` before any `get_*` call is optional — the client will auto-detect the config service URL from the `JARVIS_CONFIG_URL` environment variable if `init()` was not called explicitly.

## Lifecycle

```python
config.init(config_url="...", refresh_interval_seconds=60)

# Force an immediate refresh of the service registry
config.refresh_services()

# Shut down the background refresh thread at process exit
config.shutdown()
```

## ServiceConfig

`get_all()` returns a dict of `ServiceConfig` dataclass instances:

| Field | Description |
|-------|-------------|
| `name` | Service name (e.g. `jarvis-auth`) |
| `host` | Hostname |
| `port` | Port number |
| `url` | Full resolved URL |
| `health_path` | Health check path (e.g. `/health`) |
| `scheme` | `http` or `https` |
| `description` | Human-readable description |

## Advanced

### Database persistence

Pass a SQLAlchemy engine to persist the service registry locally, so the service can start without a live config service:

```python
config.init(config_url="...", db_engine=engine)
```

### Refresh callback

```python
def on_refresh(services: dict):
    print("Registry updated:", list(services.keys()))

config.init(config_url="...", on_refresh=on_refresh)
```

### Auto-discovery

If the config service URL is not known at startup, use `discover_config_service()` to scan the local network:

```python
from jarvis_config_client import discover_config_service
config_url = discover_config_service()
```

## Exceptions

| Exception | Raised when |
|-----------|-------------|
| `ServiceNotFoundError` | Requested service name not in registry |
| `ConfigServiceNotFoundError` | Config service URL could not be resolved |

## Configuration

| Parameter | Env Variable | Description |
|-----------|-------------|-------------|
| `config_url` | `JARVIS_CONFIG_URL` | URL of the config service |

## Caching

Service URLs are cached locally and refreshed in the background every `refresh_interval_seconds` (default 60 s). Services can tolerate brief config service outages after initial startup.

## URL Styles

The config service supports two URL styles controlled by `JARVIS_CONFIG_URL_STYLE`:

- **Default** — returns container names (e.g. `http://jarvis-auth:7701`), used by Docker services on the shared network
- **`dockerized`** — returns `host.docker.internal` URLs, used when Docker containers need to reach locally-running services (e.g. LLM proxy on macOS)
