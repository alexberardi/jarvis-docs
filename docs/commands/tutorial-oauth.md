# Tutorial: OAuth Command

This tutorial builds a command that requires OAuth authentication. You will learn how `AuthenticationConfig` works, the two OAuth modes (external and local discovery), token storage, background refresh, PKCE, and native app redirects.

**Prerequisites:** Completed the [API Integration Tutorial](tutorial-api.md).

## How OAuth Works in Jarvis

The OAuth flow in Jarvis is a collaboration between three components:

1. **Command** -- declares what auth it needs via `AuthenticationConfig`
2. **Mobile app** -- reads the config, executes the OAuth flow, sends tokens to the node
3. **Node** -- receives tokens in `store_auth_values()`, stores them as secrets

```
Mobile App                   OAuth Provider              Node
    │                             │                       │
    │  1. Read AuthenticationConfig from settings snapshot │
    │                             │                       │
    │  2. Open browser ──────────>│                       │
    │                             │                       │
    │  3. User authorizes ────────│                       │
    │                             │                       │
    │  4. Receive auth code <─────│                       │
    │                             │                       │
    │  5. Exchange code for tokens│                       │
    │     POST /token ───────────>│                       │
    │     <── access_token ───────│                       │
    │                             │                       │
    │  6. Push tokens to node ────────────────────────────>│
    │                             │                       │
    │                             │  7. store_auth_values()│
    │                             │     Save as secrets    │
```

## Mode 1: External OAuth (Known URLs)

For well-known cloud providers like Google, Spotify, or GitHub, the authorize and token URLs are known at build time.

### Example: A Spotify-like Command

```python
from typing import List

from core.ijarvis_authentication import AuthenticationConfig
from core.ijarvis_command import IJarvisCommand, CommandExample
from core.ijarvis_parameter import JarvisParameter
from core.ijarvis_secret import IJarvisSecret, JarvisSecret
from core.command_response import CommandResponse
from core.request_information import RequestInformation
from services.secret_service import get_secret_value


class PlaylistCommand(IJarvisCommand):

    @property
    def command_name(self) -> str:
        return "get_playlists"

    @property
    def description(self) -> str:
        return "List or search your Spotify playlists"

    @property
    def keywords(self) -> List[str]:
        return ["playlist", "playlists", "spotify"]

    @property
    def parameters(self) -> List[JarvisParameter]:
        return [
            JarvisParameter("query", "string", required=False, description="Search filter"),
        ]

    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return [
            JarvisSecret(
                "SPOTIFY_ACCESS_TOKEN", "Spotify OAuth access token",
                "integration", "string", friendly_name="Access Token",
            ),
            JarvisSecret(
                "SPOTIFY_REFRESH_TOKEN", "Spotify OAuth refresh token",
                "integration", "string", friendly_name="Refresh Token",
            ),
        ]

    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(
            type="oauth",
            provider="spotify",
            friendly_name="Spotify",
            client_id="your-spotify-client-id",
            keys=["access_token", "refresh_token"],

            # External OAuth -- full URLs
            authorize_url="https://accounts.spotify.com/authorize",
            exchange_url="https://accounts.spotify.com/api/token",

            # Scopes
            scopes=["playlist-read-private", "playlist-read-collaborative"],

            # PKCE for public clients (no client_secret needed)
            supports_pkce=True,

            # Background token refresh
            requires_background_refresh=True,
            refresh_interval_seconds=600,
            refresh_token_secret_key="SPOTIFY_REFRESH_TOKEN",
        )
```

### Key Fields for External OAuth

| Field | Description |
|-------|-------------|
| `authorize_url` | Full URL to the OAuth authorization endpoint |
| `exchange_url` | Full URL to the token exchange endpoint |
| `scopes` | OAuth scopes to request |
| `supports_pkce` | Set `True` for PKCE (recommended for mobile/public clients) |

## Mode 2: Local/Discoverable OAuth (Network Scan)

For services running on the local network (like Home Assistant), the URL is not known in advance. The mobile app discovers the service by scanning the network.

### Example: Home Assistant

```python
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(
            type="oauth",
            provider="home_assistant",
            friendly_name="Home Assistant",
            client_id="http://jarvis-node-mobile",
            keys=["access_token"],

            # Local OAuth -- relative paths + network discovery
            authorize_path="/auth/authorize",
            exchange_path="/auth/token",
            discovery_port=8123,
            discovery_probe_path="/api/",

            # HA does not send redirect_uri in the exchange request
            send_redirect_uri_in_exchange=False,
        )
```

### How Discovery Works

When the mobile app sees `discovery_port` in the config:

1. It scans the local network for devices with port `8123` open
2. For each candidate, it probes `http://<ip>:8123/api/` (the `discovery_probe_path`)
3. If the probe succeeds, it has found the service
4. It constructs full URLs: `http://<ip>:8123/auth/authorize`
5. After auth completes, it sends tokens plus `_base_url` to `store_auth_values()`

### Key Fields for Local OAuth

| Field | Description |
|-------|-------------|
| `authorize_path` | Relative path on the discovered host |
| `exchange_path` | Relative path for token exchange |
| `discovery_port` | Port to scan for on the LAN |
| `discovery_probe_path` | GET this path to verify it is the right service |

## Implementing `store_auth_values()`

When the mobile app completes the OAuth flow, it pushes the tokens to the node. Your command's `store_auth_values()` receives them:

```python
    def store_auth_values(self, values: dict[str, str]) -> None:
        from services.secret_service import set_secret
        from services.command_auth_service import clear_auth_flag

        if "access_token" in values:
            set_secret("SPOTIFY_ACCESS_TOKEN", values["access_token"], "integration")
        if "refresh_token" in values:
            set_secret("SPOTIFY_REFRESH_TOKEN", values["refresh_token"], "integration")

        # Clear the "needs auth" flag so the mobile app stops showing the auth prompt
        clear_auth_flag("spotify")
```

The `values` dict contains keys matching your `AuthenticationConfig.keys`. For local discovery, it also includes `_base_url` with the discovered service URL.

### Home Assistant Example (Advanced)

The HA integration does extra processing -- it creates a long-lived access token from the short-lived OAuth token:

```python
    def store_auth_values(self, values: dict[str, str]) -> None:
        from services.secret_service import set_secret

        access_token = values["access_token"]
        base_url = values["_base_url"]  # Discovered URL from network scan

        # Store the REST URL
        set_secret("HOME_ASSISTANT_REST_URL", base_url, "integration")

        # Create a long-lived access token via HA WebSocket API
        ws_url = base_url.replace("http", "ws") + "/api/websocket"
        llat = self._create_long_lived_token(ws_url, access_token)

        set_secret("HOME_ASSISTANT_API_KEY", llat, "integration")
```

## Background Token Refresh

For OAuth providers whose tokens expire, enable background refresh:

```python
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(
            # ... other fields ...
            requires_background_refresh=True,
            refresh_interval_seconds=600,      # Refresh when < 10 min remaining
            refresh_token_secret_key="SPOTIFY_REFRESH_TOKEN",
        )
```

The default `refresh_token()` implementation on `IJarvisCommand`:

1. Reads the refresh token from the secret DB
2. POSTs to `exchange_url` with `grant_type=refresh_token`
3. Passes new tokens to `store_auth_values()`
4. Stores `TOKEN_EXPIRES_AT_<PROVIDER>` in the secret DB
5. If refresh fails (401/400), flags re-auth so the mobile app prompts the user

### Custom Refresh Flow

If the provider has a non-standard refresh mechanism, override `refresh_token()`:

```python
    def refresh_token(self) -> bool:
        # Custom refresh logic
        current_token = get_secret_value("MY_REFRESH_TOKEN", "integration")
        if not current_token:
            return False

        # ... custom refresh logic ...

        self.store_auth_values({"access_token": new_token})
        return True
```

## PKCE Support

PKCE (Proof Key for Code Exchange) is the recommended flow for mobile/public clients. When `supports_pkce=True`, the mobile app automatically:

1. Generates a `code_verifier` and `code_challenge`
2. Includes `code_challenge` in the authorization request
3. Includes `code_verifier` in the token exchange request

No extra work needed in your command -- just set the flag:

```python
    supports_pkce=True,
```

## Native App Redirect

For providers that support custom URL schemes (like Google), the OAuth flow can redirect directly back to the mobile app instead of going through a web callback:

```python
    native_redirect_uri="com.googleusercontent.apps.YOUR_CLIENT_ID:/oauthredirect",
```

When `native_redirect_uri` is set:

1. The mobile app uses this as the `redirect_uri` in the authorization request
2. The provider redirects to the app's custom URL scheme after authorization
3. The mobile app catches the redirect, extracts the authorization code
4. The mobile app exchanges the code for tokens

This is more reliable than a web-based redirect because it does not depend on a callback server.

### Real-World Example: Gmail

```python
    @property
    def authentication(self) -> AuthenticationConfig:
        client_id = self._get_client_id()
        return AuthenticationConfig(
            type="oauth",
            provider="google_gmail",
            friendly_name="Gmail",
            client_id=client_id,
            keys=["access_token", "refresh_token"],
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            exchange_url="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/gmail.modify"],
            supports_pkce=True,
            extra_authorize_params={
                "access_type": "offline",
                "prompt": "consent",
            },
            requires_background_refresh=True,
            refresh_token_secret_key="GMAIL_REFRESH_TOKEN",
            native_redirect_uri=(
                f"com.googleusercontent.apps.{client_id.split('.')[0]}:/oauthredirect"
            ),
        )
```

## Extra Parameters

Some providers need additional parameters in the authorize or exchange requests:

```python
    extra_authorize_params={
        "access_type": "offline",    # Google: request a refresh token
        "prompt": "consent",         # Google: always show consent screen
    },
    extra_exchange_params={
        "audience": "https://api.example.com",  # Custom audience
    },
```

## Checking Auth Status

Use `needs_auth()` to check whether the user needs to authenticate:

```python
    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        if self.needs_auth():
            return CommandResponse.error_response(
                error_details="Please set up Gmail in your mobile app settings first.",
            )
        # ... proceed with command logic ...
```

The default `needs_auth()` implementation checks:

1. Are all required secrets present?
2. Is there a re-auth flag in the `command_auth` table? (Set when refresh fails)

## Shared Auth Across Commands

Commands with the same `provider` value share auth state. Once one command stores tokens, all commands for that provider can use them.

```python
# These two commands share "home_assistant" auth:

class ControlDeviceCommand(IJarvisCommand):
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(provider="home_assistant", ...)

class GetDeviceStatusCommand(IJarvisCommand):
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(provider="home_assistant", ...)
```

Once the user authorizes Home Assistant through either command, both commands have access to the stored tokens.

## Complete Pattern Checklist

For a fully production-ready OAuth command:

- [x] `authentication` property returns `AuthenticationConfig`
- [x] `store_auth_values()` stores all tokens as secrets
- [x] `store_auth_values()` calls `clear_auth_flag(provider)` on success
- [x] `required_secrets` lists the token secrets
- [x] `requires_background_refresh=True` if tokens expire
- [x] `refresh_token_secret_key` points to the refresh token secret
- [x] `supports_pkce=True` for public/mobile clients
- [x] `native_redirect_uri` for providers that support custom URL schemes
- [x] `needs_auth()` check in `run()` for a clean error message
