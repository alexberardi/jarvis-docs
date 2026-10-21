# Tutorial: OAuth Command

This tutorial builds a command that requires OAuth authentication. You will learn how `AuthenticationConfig` works, the two OAuth modes (external and local discovery), how the tokens reach your command, background refresh, PKCE, and native app redirects.

**Prerequisites:** Completed the [API Integration Tutorial](tutorial-api.md).

## How OAuth Works in Jarvis

Four parts take part in the flow:

1. **Command** -- declares what auth it needs via `AuthenticationConfig`
2. **Mobile app** -- reads the config from the node's settings, starts the flow and opens the provider's sign-in page; it never sees the tokens
3. **`jarvisd`** -- the redirect authority: it builds the authorize URL (state and PKCE), exchanges the code for tokens, keeps them encrypted for a few minutes and tells the node they are ready
4. **Node** -- pulls the tokens from `jarvisd` once and hands them to `store_auth_values()`, which stores them as secrets

```
Mobile App              jarvisd                  Provider            Node
    │                      │                        │                  │
    │ 1. POST /api/v0/oauth/sessions                │                  │
    │    (provider, AuthenticationConfig) ──>│      │                  │
    │ <── session id + authorize URL ──────│        │                  │
    │                      │                        │                  │
    │ 2. Open the authorize URL ───────────────────>│                  │
    │    User signs in and approves                 │                  │
    │                      │                        │                  │
    │ 3. Code comes back (to jarvisd's callback,    │                  │
    │    or to the app, which posts it to           │                  │
    │    POST .../sessions/{id}/exchange) ──>│      │                  │
    │                      │ 4. Exchange code ─────>│                  │
    │                      │ <── tokens ────────────│                  │
    │                      │    (stored encrypted)  │                  │
    │                      │                        │                  │
    │ 5. Poll GET .../sessions/{id} until active    │                  │
    │                      │                        │                  │
    │                      │ 6. MQTT jarvis/auth/{provider}/ready ────>│
    │                      │ <── 7. GET /api/v0/oauth/provider/{provider}/credentials
    │                      │ ──> tokens (one pull; then wiped) ───────>│
    │                      │                        │  8. store_auth_values()
    │                      │                        │     Save as secrets
```

## Mode 1: External OAuth (Known URLs)

For well-known cloud providers like Google, Spotify, or GitHub, the authorize and token URLs are known at build time.

### Example: A Spotify-like Command

```python
from typing import List

from jarvis_command_sdk import (
    AuthenticationConfig,
    CommandExample,
    CommandResponse,
    IJarvisCommand,
    IJarvisSecret,
    JarvisParameter,
    JarvisSecret,
    RequestInformation,
)


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

    def generate_prompt_examples(self) -> List[CommandExample]:
        return [CommandExample("What playlists do I have?", {}, is_primary=True)]

    def generate_adapter_examples(self) -> List[CommandExample]:
        return self.generate_prompt_examples()

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        token = (kwargs.get("secrets") or {}).get("SPOTIFY_ACCESS_TOKEN")
        # ... call the Spotify API with the token ...
        return CommandResponse.success_response(context_data={"message": "..."})
```

### Key Fields for External OAuth

| Field | Description |
|-------|-------------|
| `authorize_url` | Full URL to the OAuth authorization endpoint |
| `exchange_url` | Full URL to the token exchange endpoint (`jarvisd` only exchanges against a public `https` address) |
| `scopes` | OAuth scopes to request |
| `supports_pkce` | Set `True` for PKCE (recommended for public clients) |
| `client_secret` | For web-application clients: `jarvisd` sends it in the exchange instead of using PKCE |

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

            # HA does not want redirect_uri in the exchange request
            # (jarvisd ignores this flag today; see Extra Parameters)
            send_redirect_uri_in_exchange=False,
        )
```

### How Discovery Works

When the mobile app sees `discovery_port` in the config:

1. It scans the local network for devices with port `8123` open
2. For each candidate, it probes `http://<ip>:8123/api/` (the `discovery_probe_path`)
3. If the probe succeeds, it has found the service
4. It starts the session with that base URL; `jarvisd` builds the full URLs (`http://<ip>:8123/auth/authorize`) and exchanges the code against the discovered host
5. When the node pulls the tokens, `jarvisd` returns the base URL as `base_url`, and the node passes it to `store_auth_values()` as `_base_url`

### Key Fields for Local OAuth

| Field | Description |
|-------|-------------|
| `authorize_path` | Relative path on the discovered host |
| `exchange_path` | Relative path for token exchange |
| `discovery_port` | Port to scan for on the LAN |
| `discovery_probe_path` | GET this path to verify it is the right service |

## Implementing `store_auth_values()`

When `jarvisd` has the tokens it publishes `jarvis/auth/{provider}/ready` over MQTT. The node then pulls them once from `GET /api/v0/oauth/provider/{provider}/credentials` (`jarvisd` wipes them after that pull) and calls your command's `store_auth_values()`:

```python
    def store_auth_values(self, values: dict[str, str]) -> None:
        storage = JarvisStorage(self.command_name)
        if "access_token" in values:
            storage.set_secret("SPOTIFY_ACCESS_TOKEN", values["access_token"])
        if "refresh_token" in values:
            storage.set_secret("SPOTIFY_REFRESH_TOKEN", values["refresh_token"])
```

(`JarvisStorage` is imported from `jarvis_command_sdk`.) The `values` dict holds `access_token`, `refresh_token`, `token_data` (the provider's whole token response, as JSON) and, for local discovery, `_base_url` with the discovered service URL.

Only **one** component per provider gets the call: the node looks for the first command whose `authentication.provider` matches and stops there (or, when no command matches, the first device family). If several commands share a provider, the one that gets the call must store every secret the others read.

After `store_auth_values()` returns, the node clears its re-auth flag for the provider (see [Background Token Refresh](#background-token-refresh)). You don't need to do that yourself.

### Home Assistant Example (Advanced)

The HA integration does extra processing -- it creates a long-lived access token from the short-lived OAuth token:

```python
    def store_auth_values(self, values: dict[str, str]) -> None:
        storage = JarvisStorage(self.command_name)

        access_token = values["access_token"]
        base_url = values["_base_url"]  # Discovered URL from network scan

        # Store the REST URL
        storage.set_secret("HOME_ASSISTANT_REST_URL", base_url)

        # Create a long-lived access token via HA WebSocket API
        ws_url = base_url.replace("http", "ws") + "/api/websocket"
        llat = self._create_long_lived_token(ws_url, access_token)

        storage.set_secret("HOME_ASSISTANT_API_KEY", llat)
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

On the Python node, a background agent (`TokenRefreshAgent`) does the refreshing. Every 5 minutes, for each provider that some command or device family marks `requires_background_refresh` (once per provider, however many commands share it):

1. It reads `TOKEN_EXPIRES_AT_<PROVIDER>` from the node's secrets. When that expiry is less than `refresh_interval_seconds` away, or not recorded at all (as after the first sign-in), it refreshes.
2. It reads the refresh token from the secret named by `refresh_token_secret_key`.
3. If your command overrides `refresh_token()`, it calls your override. Otherwise it does the standard OAuth2 `refresh_token` grant itself, POSTing to `exchange_url` with `client_id` (and `client_secret`, if set).
4. It passes the new tokens to `store_auth_values()` (`access_token`, plus `refresh_token` when the provider sent a new one) and stores the new expiry, when the provider gave one.
5. When the refresh can't succeed without the user (no refresh token stored, the provider answers 400 or 401, no access token in the reply, or your override returns `None` or no access token), it flags the provider for re-authentication: the node's settings snapshot then marks the provider `needs_auth` with the reason. (The mobile app does not show that flag yet.) Other failures (a timeout, a 5xx, your override raising) are only logged and retried on the next cycle.
6. A successful refresh clears that flag.

When the refresh-token secret is `scope="user"`, the agent refreshes each user's token separately, with that user set as the current user around your override and `store_auth_values()`. The re-auth flag is per provider, so one user's failed refresh flags the provider for everyone until it is reconnected.

### Custom Refresh Flow

If the provider has a non-standard refresh mechanism, override `refresh_token()`. Return a `TokenBundle`, or `None` when the refresh failed:

```python
from jarvis_command_sdk import TokenBundle

    def refresh_token(self, *, refresh_token, client_secret=None,
                      timeout_seconds=15.0) -> TokenBundle | None:
        if not refresh_token:
            return None

        # ... custom refresh logic producing new_token and its lifetime ...

        return TokenBundle(
            access_token=new_token,
            refresh_token=refresh_token,  # or the new one, if the provider rotated it
            expires_in=3600,              # seconds, or None if unknown
        )
```

`expires_in` has no default; pass `None` when the provider doesn't say. Don't raise for a refused refresh: return `None`, which flags re-auth. The node calls the override with `refresh_token` and `client_secret` only, so keep the other arguments' defaults.

## PKCE Support

PKCE (Proof Key for Code Exchange) is the recommended flow for public clients. When `supports_pkce=True`, `jarvisd`:

1. Generates a `code_verifier` and `code_challenge` when the session starts
2. Includes `code_challenge` in the authorize URL it hands to the mobile app
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

1. It is used as the `redirect_uri` in the authorization request
2. The provider redirects to the app's custom URL scheme after authorization
3. The mobile app catches the redirect and extracts the authorization code
4. The mobile app posts the code to `jarvisd` (`POST /api/v0/oauth/sessions/{id}/exchange`), and `jarvisd` exchanges it for tokens

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

!!! note "Exchange extras are ignored on jarvisd"
    `jarvisd` uses `extra_authorize_params`, but it accepts and ignores `extra_exchange_params` and `send_redirect_uri_in_exchange`, as the old server did: the exchange always sends `code`, `client_id`, `redirect_uri` and, when set, `client_secret` and `code_verifier`.

## Checking Auth Status

Use `needs_auth()` to check whether the user needs to authenticate:

```python
    def run(self, request_info: RequestInformation, *,
            secrets: dict[str, str] | None = None, **kwargs) -> CommandResponse:
        if self.needs_auth(secrets=secrets or {}):
            return CommandResponse.error_response(
                error_details="Please set up Gmail in your mobile app settings first.",
            )
        # ... proceed with command logic ...
```

`secrets` is passed only when the host passes it to `execute()` (the node always does), so give it a default: a test that calls `run()` without it would otherwise fail with a `TypeError`.

The default `needs_auth(*, secrets, auth_status=None)` implementation checks:

1. Are all required secrets present in the host-supplied `secrets` dict?
2. Does the optional host-supplied `auth_status` flag re-auth? The Python node does not pass `auth_status` today, so on the node only the first check applies; the node keeps its own re-auth flag (set by a failed background refresh) in its settings snapshot instead.

## Shared Auth Across Commands

Commands with the same `provider` value share auth state. Once one command stores tokens, all commands for that provider can use them.

```python
# These two commands share "google_gmail" auth:

class ReadEmailCommand(IJarvisCommand):
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(provider="google_gmail", ...)

class SendEmailCommand(IJarvisCommand):
    @property
    def authentication(self) -> AuthenticationConfig:
        return AuthenticationConfig(provider="google_gmail", ...)
```

Once the user connects Gmail through either command, both can read the stored tokens. Remember that only one of them gets the `store_auth_values()` call, so both must read the same secret keys.

## Complete Pattern Checklist

For a fully production-ready OAuth command:

- [x] `authentication` property returns `AuthenticationConfig`
- [x] `store_auth_values()` stores all tokens as secrets (every key the provider's other commands read)
- [x] `required_secrets` lists the token secrets
- [x] `requires_background_refresh=True` if tokens expire
- [x] `refresh_token_secret_key` points to the refresh token secret
- [x] `supports_pkce=True` for public clients
- [x] `native_redirect_uri` for providers that support custom URL schemes
- [x] `needs_auth(secrets=...)` check in `run()` for a clean error message
