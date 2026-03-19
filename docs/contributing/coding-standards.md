# Coding Standards

## Working Style

**Be a scalpel, not a hammer.**

- Ask questions early when stuck or uncertain, rather than repeatedly trying the same approach
- If something fails 2-3 times, step back and re-evaluate
- Precision over persistence -- one well-aimed question beats five failed attempts

## Language and Framework

- **Python 3.11+** for all backend services
- **FastAPI + Uvicorn** for all HTTP services
- **Docker + Docker Compose** for containerization
- **TypeScript** for the mobile app (React Native/Expo)

## Imports

All imports must be at the top of the file. No mid-file imports unless absolutely necessary (e.g., circular import resolution).

Group imports in this order:

1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
import os
from datetime import datetime, timezone
from typing import Any

# Third-party
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local
from app.core.config import settings
from app.services.memory_service import MemoryService
```

## Type Hints

Always use type hints on every function parameter, return type, and variable declaration. No ambiguous signatures.

```python
# Good
def process_command(text: str, user_id: int, timeout: float = 5.0) -> CommandResponse | None:
    count: int = 0
    results: list[dict[str, Any]] = []
    ...

# Bad
def process_command(text, user_id, timeout=5.0):
    count = 0
    results = []
    ...
```

Prefer `X | None` over `Optional[X]` (Python 3.10+ syntax). Use the `typing` module for complex types (`TypeVar`, `Protocol`, etc.).

## Logging

All logging must go through `jarvis-log-client` to the `jarvis-logs` service. No `print()` statements in production code.

```python
from jarvis_log_client import JarvisLogger

logger = JarvisLogger("my-service")

logger.info("Processing command", extra={"user_id": user_id, "command": command_name})
logger.error("Command failed", extra={"error": str(e)}, exc_info=True)
```

The only acceptable uses of `print()` are:

- CLI scripts (e.g., `install_command.py`, `authorize_node.py`)
- Test files
- Worker `_safe_print()` pattern (for pre-logger-init output)

## Exception Handling

- Never use bare `except:` -- always catch specific exception types
- Always capture the exception with `as e` when using `except Exception`
- Prefer specific exceptions (`ValueError`, `httpx.HTTPError`) over broad `Exception`

```python
# Good
try:
    result = await client.post(url, json=payload)
    result.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.error("HTTP error", extra={"status": e.response.status_code})
except httpx.RequestError as e:
    logger.error("Connection error", extra={"error": str(e)})

# Bad
try:
    result = await client.post(url, json=payload)
except:
    pass
```

## New Services

When creating a new service:

1. Use Docker containers with `Dockerfile` and `docker-compose.yaml`
2. Follow existing service patterns (FastAPI + Uvicorn)
3. Include a `CLAUDE.md` with service-specific documentation
4. Add health check endpoint at `/health`
5. Use Alembic for database migrations
6. Register with `jarvis-config-service` for service discovery
7. Use `jarvis-log-client` for logging
8. Add the service to the CLI's service registry in the `jarvis` script

## Code Quality

- Target 80%+ test coverage for all services
- Run `pytest` before committing
- Use `ruff` for linting (configured at the project level)
- Keep files under 500 lines -- split into modules if growing larger
