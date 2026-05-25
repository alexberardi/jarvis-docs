# Log Client

The log client library provides `JarvisLogger`, the standard way for all Jarvis services to emit structured logs. It sends log entries to the centralized [Logs service](../services/logs.md) over HTTP, with automatic fallback to console output if the logs service is unavailable.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-log-client` |
| **Source** | `jarvis-log-client/` |
| **Backend** | jarvis-logs (port 7702) |

## Usage

Credentials are registered once at startup via `init()`, then a `JarvisLogger` instance is created per service:

```python
from jarvis_log_client import init, JarvisLogger

# Call once at startup (module level)
init(app_id="my-service", app_key="secret-key")

logger = JarvisLogger(
    service="my-service",
    console_level="INFO",
    remote_level="DEBUG",
)

# Structured context fields are passed as keyword arguments
logger.info("Processing request", user_id=42, action="search")
logger.error("Failed to connect", target="database")
```

For node authentication instead of app auth, use `init_node()`:

```python
from jarvis_log_client import init_node
init_node(node_id="my-node", node_key="node-secret")
```

## JarvisLogHandler (alternative)

For services that already use Python's standard `logging` module, attach `JarvisLogHandler` to an existing logger instead:

```python
import logging
from jarvis_log_client import init, JarvisLogHandler

init(app_id="my-service", app_key="secret-key")
handler = JarvisLogHandler(service="my-service", level=logging.DEBUG)
logging.getLogger("uvicorn").addHandler(handler)
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `service` | *(required)* | Service name attached to every log entry |
| `server_url` | `JARVIS_LOGS_URL` env | URL of the logs service |
| `console_level` | `"INFO"` | Log level for console output |
| `remote_level` | `"DEBUG"` | Log level for remote (Loki) output |
| `batch_size` | `50` | Max log entries per batch before flush |
| `flush_interval` | `5.0` | Seconds between automatic batch flushes |

## Log Levels

Standard Python log levels are supported: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Structured Fields

Every log entry includes:

| Field | Description |
|-------|-------------|
| `service` | Service name (set at init) |
| `level` | Log level |
| `message` | Log message |
| `timestamp` | ISO 8601 timestamp |
| Additional kwargs | Arbitrary key-value context fields passed at call site |

## Health and Status

```python
# Check whether remote logging is active
if logger.is_remote_disabled:
    print("Remote logging is off (auth failure or logs service down)")

# Inspect remote connection status
status = logger.get_remote_status()
```

The client will disable remote logging after 10 consecutive auth failures and will not retry, to avoid flooding the console with auth errors.

## Fallback Behavior

If the logs service is unreachable, `JarvisLogger` automatically falls back to standard console output (stdout). No log entries are lost during the current process, but they will not appear in Loki/Grafana until the service is restored. The client uses exponential backoff when retrying failed deliveries.

## Rules

- **All production code must use `JarvisLogger`** — no `print()` statements for logging
- CLI scripts, test files, and worker `_safe_print()` patterns are exempt
