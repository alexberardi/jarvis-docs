# Auth Client

The auth client library provides middleware and helper functions for validating authentication in Jarvis services. It supports all three auth modes: app-to-app, node, and user JWT.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-auth-client` |
| **Source** | `jarvis-auth-client/` |
| **Backend** | jarvis-auth (port 7701) |

## Auth Modes

### App-to-App

Used for service-to-service communication. Validates `X-Jarvis-App-Id` and `X-Jarvis-App-Key` headers against the auth service.

```python
from jarvis_auth_client import validate_app_request

# In a FastAPI dependency
async def require_app_auth(request: Request):
    result = await validate_app_request(
        request,
        auth_base_url="http://jarvis-auth:7701",
    )
    if not result.valid:
        raise HTTPException(status_code=401)
```

### Node Auth

Used for Pi Zero nodes connecting to services. Validates `X-API-Key` header (format: `node_id:node_key`).

### User JWT

Used for end-user requests (admin UI, mobile app). Validates `Authorization: Bearer <jwt>` header.

## Configuration

| Parameter | Env Variable | Description |
|-----------|-------------|-------------|
| `auth_base_url` | `JARVIS_AUTH_BASE_URL` | URL of the auth service |

## Consumers

Used by nearly every service that accepts authenticated requests:

- jarvis-command-center, jarvis-whisper-api, jarvis-tts, jarvis-ocr-service, jarvis-recipes-server, jarvis-logs, jarvis-notifications, jarvis-config-service, jarvis-settings-server, jarvis-admin
