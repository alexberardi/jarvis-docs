# Auth Client

The auth client library provides FastAPI dependencies and helper functions for validating authentication in Jarvis services. It supports all three auth modes: app-to-app, node, and user JWT.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-auth-client` |
| **Source** | `jarvis-auth-client/` |
| **Backend** | jarvis-auth (port 7701) |

## Initialization

Call `init()` once at startup before using any auth dependencies:

```python
import jarvis_auth_client as auth_client

auth_client.init(auth_base_url="http://jarvis-auth:7701")
```

The auth URL can also be set via the `JARVIS_AUTH_BASE_URL` environment variable; `init()` picks it up automatically.

## Auth Modes

### App-to-App

Used for service-to-service communication. `require_app_auth()` is a **dependency factory** — call it to produce a FastAPI `Depends`-compatible dependency:

```python
from fastapi import FastAPI, Depends
from jarvis_auth_client.fastapi import require_app_auth
from jarvis_auth_client.models import AppAuthResult

app = FastAPI()
_verify = require_app_auth()

@app.post("/transcribe")
async def transcribe(auth: AppAuthResult = Depends(_verify)):
    # auth.app.app_id, auth.context.household_id, etc.
    ...
```

Incoming requests must include:

```
X-Jarvis-App-Id: my-service
X-Jarvis-App-Key: secret-key
```

The `AppAuthResult` carries:

| Field | Description |
|-------|-------------|
| `auth.app.app_id` | Calling service identity |
| `auth.context.household_id` | Resolved household context |
| `auth.context.node_id` | Resolved node context |
| `auth.context.user_id` | Resolved user context |
| `auth.context.household_member_ids` | List of member IDs in the household |

### Node Auth

Used for Pi Zero nodes connecting to services. Nodes send a single combined `X-API-Key` header:

```
X-API-Key: <node_id>:<node_key>
```

The service forwards this header to jarvis-auth's `/internal/validate-node` endpoint to validate the credentials and resolve the node's household, user, and per-service access.

### User JWT

Used for end-user requests (admin UI, mobile app). Validates `Authorization: Bearer <jwt>`.

### Superuser JWT

For admin-only endpoints, use `require_superuser`:

```python
from jarvis_auth_client.fastapi import require_superuser
from jarvis_auth_client.models import SuperuserUser

@app.get("/admin/users")
async def list_users(user: SuperuserUser = Depends(require_superuser)):
    ...
```

## Context Headers

Services pass context downstream using these headers, populated from the `AppAuthResult.context`:

| Header | Description |
|--------|-------------|
| `X-Context-Household-Id` | Household the request belongs to |
| `X-Context-Node-Id` | Node the request originated from |
| `X-Context-User-Id` | Authenticated user ID |
| `X-Context-Household-Member-Ids` | Comma-separated member IDs |

## Validation Caching

Auth validation results are cached in memory to avoid hitting the auth service on every request. Default TTL: 60 seconds (configurable). Call `clear_validation_cache()` to invalidate immediately.

## Configuration

| Parameter / Env Variable | Description |
|--------------------------|-------------|
| `JARVIS_AUTH_BASE_URL` | URL of the auth service |
| `JARVIS_AUTH_CACHE_SUCCESS_TTL` | Success result cache TTL in seconds (default `300`) |
| `JARVIS_AUTH_CACHE_FAILURE_TTL` | Failure result cache TTL in seconds (default `60`) |

## Lifecycle

```python
# Initialize at startup
auth_client.init(auth_base_url="http://jarvis-auth:7701")

# Manual credential validation (outside FastAPI context)
result = await auth_client.validate_app_credentials(app_id="...", app_key="...")

# Clear cache
auth_client.clear_validation_cache()

# Cleanup at shutdown
await auth_client.shutdown()
```

## Consumers

Used by nearly every service that accepts authenticated requests:

- jarvis-command-center, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-logs, jarvis-notifications, jarvis-config-service, jarvis-settings-server, jarvis-admin
