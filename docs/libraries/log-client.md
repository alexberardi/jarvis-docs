# Log Client

The log client library provides `JarvisLogger`, the standard way for all Jarvis services to emit structured logs. It sends log entries to the centralized [Logs service](../services/logs.md) over HTTP, with automatic fallback to console output if the logs service is unavailable.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-log-client` |
| **Source** | `jarvis-log-client/` |
| **Backend** | jarvis-logs (port 7702) |

## Usage

```python
from jarvis_log_client import JarvisLogger

logger = JarvisLogger(
    service_name="my-service",
    logs_url="http://jarvis-logs:7702",
    app_id="my-service",
    app_key="secret-key",
)

logger.info("Processing request", extra={"user_id": 42, "action": "search"})
logger.error("Failed to connect", extra={"target": "database"})
```

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
| `extra` | Arbitrary key-value metadata |

## Configuration

The logger is configured via constructor arguments, typically sourced from environment variables:

| Parameter | Env Variable | Description |
|-----------|-------------|-------------|
| `service_name` | -- | Identifies the source service |
| `logs_url` | `JARVIS_LOGS_URL` | URL of the logs service |
| `app_id` | `JARVIS_AUTH_APP_ID` | App-to-app auth ID |
| `app_key` | `JARVIS_AUTH_APP_KEY` | App-to-app auth key |

## Fallback Behavior

If the logs service is unreachable, `JarvisLogger` automatically falls back to standard console output (stdout). No log entries are lost during the current process, but they will not appear in Loki/Grafana until the service is restored.

## Rules

- **All production code must use `JarvisLogger`** -- no `print()` statements for logging
- CLI scripts, test files, and worker `_safe_print()` patterns are exempt
