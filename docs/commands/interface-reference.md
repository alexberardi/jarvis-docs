# Interface Reference

Complete reference for `IJarvisCommand` and all supporting classes. This is the authoritative guide to every property, method, and dataclass in the command system.

## Class Hierarchy

```
IJarvisCommand (ABC)
  └── YourCommand (concrete)
```

`IJarvisCommand` provides the `execute()` orchestration (validation, auto-correction, then `run()`) plus the full property interface -- command name, description, parameters, secrets, examples, and all optional hooks.

Everything on this page is imported from `jarvis_command_sdk` (installed from git: `pip install git+https://github.com/alexberardi/jarvis-command-sdk.git`; see [jarvis-command-sdk](../libraries/command-sdk.md)). The command runs on the node; `jarvisd` only runs the model turn (see [Execution Lifecycle](lifecycle.md)).

---

## Abstract Properties (Required)

These must be implemented by every command.

### `command_name -> str`

Unique identifier for this command. Used as the tool name in the LLM schema, in test filters, and in the secrets database.

```python
@property
def command_name(self) -> str:
    return "get_weather"
```

**Rules:**

- Must be unique across all commands on a node
- Use `snake_case`
- Keep it short and descriptive

### `description -> str`

Human-readable description sent to the LLM as the tool description. This is the primary signal the LLM uses to decide whether to call this command.

```python
@property
def description(self) -> str:
    return "Weather conditions or forecast (up to 5 days). Use for ALL weather queries."
```

**Tips:**

- Be specific about what this command handles vs. what it does not
- Mention edge cases the LLM should know about
- If the LLM confuses this with another command, add clarification here

### `parameters -> List[IJarvisParameter]`

Parameter definitions. These become the tool's JSON Schema for the LLM, and are validated by the execution pipeline.

```python
@property
def parameters(self) -> List[JarvisParameter]:
    return [
        JarvisParameter("city", "string", required=False, description="City name"),
        JarvisParameter("unit_system", "string", required=False, enum_values=["metric", "imperial"]),
    ]
```

See [Parameters Deep Dive](parameters.md) for complete documentation.

### `required_secrets -> List[IJarvisSecret]`

Secrets this command needs at runtime. Validated before `run()` is called -- if any required secret is missing, a `MissingSecretsError` is raised.

```python
@property
def required_secrets(self) -> List[IJarvisSecret]:
    return [
        JarvisSecret("OPENWEATHER_API_KEY", "API key", "integration", "string"),
    ]
```

See [Secrets Deep Dive](secrets.md) for complete documentation.

### `keywords -> List[str]`

Keywords for fuzzy matching. Used during command discovery and as hints to the LLM.

```python
@property
def keywords(self) -> List[str]:
    return ["weather", "forecast", "temperature", "rain", "snow", "wind"]
```

### `generate_prompt_examples() -> List[CommandExample]`

Concise examples included in the LLM system prompt. These teach the LLM how to extract parameters from natural language.

```python
def generate_prompt_examples(self) -> List[CommandExample]:
    return [
        CommandExample(
            voice_command="What's the weather in Chicago?",
            expected_parameters={"city": "Chicago"},
            is_primary=True,
        ),
        CommandExample(
            voice_command="How's the weather?",
            expected_parameters={},
        ),
    ]
```

**Rules:**

- At most **1** example may have `is_primary=True`
- Keep this list small (3-7 examples) -- it goes into every prompt

### `generate_adapter_examples() -> List[CommandExample]`

A larger, more varied set of examples (10-20) used to train adapters. It is abstract like the others: a command without it can't be instantiated, and the node skips it. If you have nothing extra, return the prompt examples:

```python
def generate_adapter_examples(self) -> List[CommandExample]:
    return self.generate_prompt_examples()
```

### `run(request_info, **kwargs) -> CommandResponse`

The actual command logic. Called after all validation passes.

```python
def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
    city = kwargs.get("city", "New York")
    # ... do work ...
    return CommandResponse.success_response(
        context_data={"temperature": 72, "city": city}
    )
```

**Arguments:**

- `request_info`: A `RequestInformation` object with the original voice command, conversation ID, user, and validation context
- `**kwargs`: Validated parameters extracted by the LLM, matching your `parameters` definitions
- `secrets` (in `kwargs`): when the host passes a `secrets` dict to `execute()`, it is forwarded to `run()` as the `secrets` keyword. The Python node always passes it: the values of your `required_secrets` that are set. It is absent when `execute()` is called without it (in tests, for example), so read it with `kwargs.get("secrets") or {}`.

---

## Optional Properties (Overridable)

These have sensible defaults. Override only when needed.

### `rules -> List[str]`

General rules included in the command schema for the LLM. Use for behavioral guidance.

```python
@property
def rules(self) -> List[str]:
    return [
        "Use 'resume' not 'play' when continuing paused music",
        "Default action is 'list' for email",
    ]
```

**Default:** `[]`

### `critical_rules -> List[str]`

Must-follow rules. Formatted with extra emphasis in the prompt to the LLM.

```python
@property
def critical_rules(self) -> List[str]:
    return [
        "NEVER send an email without explicit user intent",
        "Map terms: plus/sum -> 'add', minus -> 'subtract'",
    ]
```

**Default:** `[]`

### `antipatterns -> List[CommandAntipattern]`

Commands that the LLM should NOT confuse with this one. Helps with disambiguation.

```python
@property
def antipatterns(self) -> List[CommandAntipattern]:
    return [
        CommandAntipattern(
            command_name="get_current_time",
            description="Time queries like 'What time is it?' Use get_current_time."
        ),
    ]
```

**Default:** `[]`

### `allow_direct_answer -> bool`

Whether the LLM may respond directly to the user without calling this tool. Useful for commands like `calculate` where the LLM might already know the answer.

```python
@property
def allow_direct_answer(self) -> bool:
    return True
```

**Default:** `False`

### `is_risky -> bool`

Whether running this command has consequences that are hard to undo: it spends money, contacts someone, or changes something outside the home. Errands treat a new risky step as a change that needs your approval, and a risky command can only run without a tap through an explicit household rule.

```python
@property
def is_risky(self) -> bool:
    return True
```

**Default:** `False`

### `run_without_confirmation -> bool`

Whether this command is safe to run in the background without anyone tapping to approve it, when no household rule says otherwise. Use it for read-only lookups (weather, drive time, search) and for small, reversible actions on the node itself (a reminder, a timer, a list item). It is ignored for commands that are `is_risky` or that take a `business` argument.

```python
@property
def run_without_confirmation(self) -> bool:
    return True
```

**Default:** `False`

!!! note "Coming with the SDK release"
    The Python SDK and node-setup send this property in a coming release. Until then, commands on Python nodes always ask. The Go desktop node already sends it.

### `required_packages -> List[JarvisPackage]`

Pip dependencies for this command. At install time, `install_command.py` collects all `required_packages` from enabled commands, checks for version conflicts against each other and against `requirements.txt`, and writes the merged result to `custom-requirements.txt`.

```python
from jarvis_command_sdk import JarvisPackage

@property
def required_packages(self) -> List[JarvisPackage]:
    return [
        JarvisPackage("music-assistant-client", ">=1.3.0"),
    ]
```

If two commands declare incompatible version constraints for the same package, `install_command.py` fails with a clear error showing which commands conflict and what specs are incompatible.

**Default:** `[]`

### `associated_service -> str | None`

Logical grouping name for the mobile settings UI. Commands sharing the same `associated_service` are grouped together.

```python
@property
def associated_service(self) -> str | None:
    return "OpenWeather"
```

**Default:** Returns `authentication.friendly_name` if auth is configured, otherwise `None`.

### `authentication -> AuthenticationConfig | None`

OAuth configuration. Commands sharing the same `provider` string share auth state -- once one command completes OAuth, all commands with that provider see the tokens.

```python
from jarvis_command_sdk import AuthenticationConfig

@property
def authentication(self) -> AuthenticationConfig | None:
    return AuthenticationConfig(
        type="oauth",
        provider="google_gmail",
        friendly_name="Gmail",
        client_id="your-client-id",
        keys=["access_token", "refresh_token"],
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        exchange_url="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        supports_pkce=True,
    )
```

**Default:** `None`

See [OAuth Command Tutorial](tutorial-oauth.md) for full details.

### `all_possible_secrets -> List[IJarvisSecret]`

All secrets this command could ever need across all configuration variants. Used by `install_command.py` to seed the database upfront. Override when `required_secrets` is config-dependent (e.g., different secrets for Gmail vs. IMAP).

```python
@property
def all_possible_secrets(self) -> List[IJarvisSecret]:
    return [
        JarvisSecret("EMAIL_PROVIDER", "Provider", "integration", "string", required=False),
        JarvisSecret("GMAIL_ACCESS_TOKEN", "Token", "integration", "string"),
        JarvisSecret("IMAP_USERNAME", "Username", "integration", "string"),
        # ... all variants
    ]
```

**Default:** Delegates to `required_secrets`.

### `setup_guide -> str | None`

Markdown shown in the mobile app when the user taps "Setup Help" on the command's settings: how to get an API key, enable an integration, and so on.

**Default:** `None`

### `supported_platforms -> List[str]`

Platforms the command runs on, e.g. `["darwin"]` for a macOS-only command. An empty list means all.

**Default:** `[]`

### `fast_path_patterns -> List[FastPathPattern]`

Regex patterns the command claims for the fast path (no model turn). The default `pre_route()` tries them; the mobile app lists them so the user can turn single patterns off. See `pre_route()` under Lifecycle Methods below.

**Default:** `[]`

### Other optional members

The SDK has more optional members than this page covers: `proposable_actions` and `listening_signal_types` (errands and signals), the data-browser members (`data_browser_storage_name`, `editable_fields`, `display_summary`, ...) that let the mobile app edit records the command keeps in `JarvisStorage`, and `context_operations`. Their docstrings in `jarvis_command_sdk/command.py` describe them.

---

## Running without a tap (household rules)

Live voice turns never use these rules: a person is right there. Background work does: errands, signal automations and watches. For each action Jarvis checks these in order, and the first match wins:

1. a rule set for that particular watch or goal;
2. a household rule for the command, set by a household admin (allow, ask or block);
3. the command's own `run_without_confirmation`;
4. otherwise it asks.

Nothing runs on its own until the household turns on background errands, and everything that ran on its own shows up in the app as a "Ran on its own" card.

---

## Lifecycle Methods

These methods participate in the command execution pipeline. See [Execution Lifecycle](lifecycle.md) for the full flow.

### `pre_route(voice_command, *, disabled_pattern_ids=frozenset()) -> PreRouteResult | None`

Fast-path routing that bypasses the LLM entirely. The node calls it on every command before it contacts `jarvisd`; the first command that returns a result wins, and the node runs it with `request_info.is_pre_routed=True`.

The usual way in is to declare `fast_path_patterns` and let the default `pre_route()` match them. Each pattern names a handler method on the command, called as `handler(match, voice_command)`:

```python
import re

from jarvis_command_sdk import FastPathPattern, PreRouteResult


@property
def fast_path_patterns(self) -> List[FastPathPattern]:
    return [
        FastPathPattern(
            id="music.pause",               # stable across versions
            description="Pause playback",
            example="pause the music",
            regex=r"^pause( the music)?$",
            handler="_pre_route_pause",
        ),
    ]

def _pre_route_pause(self, match: re.Match, voice_command: str) -> PreRouteResult | None:
    return PreRouteResult(arguments={"action": "pause"})
```

The user can turn single patterns off in the mobile app; the node passes their ids as `disabled_pattern_ids`. If you override `pre_route()` for parsing a regex can't do, keep the signature and honour that set:

```python
def pre_route(self, voice_command: str, *, disabled_pattern_ids=frozenset()) -> PreRouteResult | None:
    if "music.pause" in disabled_pattern_ids:
        return None
    text = voice_command.lower().strip()
    if text in ("pause", "pause the music"):
        return PreRouteResult(arguments={"action": "pause"})
    return None  # Fall through to the LLM
```

**Returns:** `PreRouteResult` with `arguments` dict and optional `spoken_response`, or `None` to use the normal LLM path. On the fast path no model writes the reply, so put the sentence to speak in `context_data["message"]` (or `spoken_response`).

### `post_process_tool_call(args, voice_command) -> dict`

Fix up LLM tool-call arguments before execution. Called after the LLM produces a tool call but before `execute()`. Use to patch common LLM mistakes.

```python
def post_process_tool_call(self, args: dict, voice_command: str) -> dict:
    if args.get("action") == "delete":
        args["action"] = "trash"  # Normalize "delete" to "trash"
    return args
```

**Default:** Returns `args` unchanged.

### `validate_call(**kwargs) -> list[ValidationResult]`

Custom parameter validation after basic type and presence checks pass. Override for cross-parameter validation, context-dependent checks, or entity resolution.

```python
from jarvis_command_sdk import ValidationResult

def validate_call(self, **kwargs) -> list[ValidationResult]:
    results = super().validate_call(**kwargs)  # Run default enum/type checks
    entity_id = kwargs.get("entity_id")
    if entity_id and not self._entity_exists(entity_id):
        results.append(ValidationResult(
            success=False,
            param_name="entity_id",
            command_name=self.command_name,
            message=f"Device '{entity_id}' not found",
            valid_values=self._get_known_entities(),
        ))
    return results
```

**Default:** Iterates `parameters`, calls `param.validate(value)` on each.

### `handle_action(action_name, context) -> CommandResponse`

Handle interactive button taps from the mobile app. When a user taps a button on a response that included `actions`, `jarvisd` forwards the tap to the node over MQTT, and the node calls this method and posts the result back.

```python
def handle_action(self, action_name: str, context: dict) -> CommandResponse:
    if action_name == "send_click":
        # Send the email draft from context
        self._send_email(context["draft"])
        return CommandResponse.final_response(
            context_data={"message": "Email sent."}
        )
    return super().handle_action(action_name, context)  # Handles cancel_click
```

**Default:** Handles `cancel_click` automatically. Returns error for unknown actions.

### `store_auth_values(values) -> None`

Called on the node when `jarvisd` delivers new OAuth tokens (after the user connects the account in the mobile app), and again after each background refresh. Override to store the tokens as secrets.

```python
from jarvis_command_sdk import JarvisStorage

def store_auth_values(self, values: dict[str, str]) -> None:
    storage = JarvisStorage(self.command_name)
    if "access_token" in values:
        storage.set_secret("GMAIL_ACCESS_TOKEN", values["access_token"])
    if "refresh_token" in values:
        storage.set_secret("GMAIL_REFRESH_TOKEN", values["refresh_token"])
```

Only one command per provider gets the call; see [OAuth Command Tutorial](tutorial-oauth.md#implementing-store_auth_values).

**Default:** No-op.

### `refresh_token(*, refresh_token, client_secret=None, timeout_seconds=15.0) -> TokenBundle | None`

Refresh an OAuth2 access token. The default implementation is a pure HTTP call: it POSTs to `auth.exchange_url` with `grant_type=refresh_token` and returns a `TokenBundle` (`access_token`, `refresh_token`, `expires_in`, `raw`) on success, or `None` if the command has no authentication config or the HTTP call fails. The method itself does not touch the secret store.

Override it for non-standard refresh flows. The Python node's background refresh (for `requires_background_refresh=True`) calls your override when you have one, otherwise it does the standard grant itself; either way it hands the new tokens to `store_auth_values()`. See [Background Token Refresh](tutorial-oauth.md#background-token-refresh).

### `needs_auth(*, secrets, auth_status=None) -> bool`

Whether the user needs to (re)connect the account. Pure check against the host-supplied `secrets` dict: returns `True` when a required secret is missing or when the optional `auth_status` flags re-auth. Commands with no `authentication` config return `False`. The Python node does not pass `auth_status` today; it keeps its own re-auth flag (set when a background refresh fails) in its settings snapshot.

### `init_data() -> dict`

One-time initialization hook. Run it by hand from a shell on the node: `python scripts/init_data.py --command <name>`. Use for first-install setup like registering devices or fetching initial state.

```python
def init_data(self) -> dict:
    # Fetch and cache initial device list
    devices = self._fetch_devices()
    return {"status": "success", "devices_found": len(devices)}
```

**Default:** Returns `{"status": "no_init_required"}`.

---

## The `execute()` Method

You do not override `execute()` -- it is the orchestration method on `IJarvisCommand` that calls your hooks in order. The host passes in a `secrets` dict built from its secret store (or `None` to skip secret enforcement, e.g. in tests):

```python
def execute(self, request_info, *, secrets=None, **kwargs) -> CommandResponse:
    if secrets is not None:        # Check all required secrets present
        missing = [s.key for s in self.required_secrets
                   if s.required and not secrets.get(s.key)]
        if missing:
            raise MissingSecretsError(missing)
    # Check required params present (raises ValueError on omissions)
    image_errors = self._coerce_image_params(kwargs)  # "image" params -> list[JarvisImage]
    if image_errors:
        return CommandResponse.validation_error(image_errors)
    results = self.validate_call(**kwargs)  # Value validation
    errors = [r for r in results if not r.success]
    if errors:
        return CommandResponse.validation_error(errors)
    for r in results:              # Apply auto-corrections
        if r.suggested_value is not None:
            kwargs[r.param_name] = r.suggested_value
    if secrets is not None:        # Forwarded only when given
        return self.run(request_info, secrets=secrets, **kwargs)
    return self.run(request_info, **kwargs)
```

---

## Related Classes

### `CommandExample`

```python
@dataclass
class CommandExample:
    voice_command: str              # "What's the weather in Chicago?"
    expected_parameters: dict       # {"city": "Chicago"}
    is_primary: bool = False        # At most 1 per example list
```

### `CommandAntipattern`

```python
@dataclass
class CommandAntipattern:
    command_name: str    # "get_current_time"
    description: str     # "Time queries like 'What time is it?'"
```

### `PreRouteResult`

```python
@dataclass
class PreRouteResult:
    arguments: dict                 # kwargs to pass to execute()
    spoken_response: str | None = None  # Optional TTS override
```

### `RequestInformation`

```python
@dataclass
class RequestInformation:
    voice_command: str                          # Original utterance
    conversation_id: str                        # Conversation session ID
    is_validation_response: bool = False        # True if this is a clarification reply
    validation_context: dict | None = None      # Context from validation flow
    user_id: int | None = None                  # The speaker, when known
    is_pre_routed: bool = False                 # True on the fast path: no LLM writes the reply
    home_context: dict | None = None            # Household info from jarvisd, e.g. {"location": ...}
```

When `is_pre_routed` is `True`, put the full sentence to speak in `context_data["message"]`.

### `CommandResponse`

See [Response Patterns](responses.md) for full documentation. Quick reference:

| Factory Method | Success | Wait for Input | Use Case |
|----------------|---------|----------------|----------|
| `success_response()` | `True` | `True` | Standard success |
| `with_items()` | `True` | `True` | A list the user can act on next ("mark those as read") |
| `error_response()` | `False` | `False` | Errors |
| `follow_up_response()` | `True` | `True` | Expects more user input |
| `final_response()` | `True` | `False` | One-shot, conversation ends |
| `chunked_response()` | `True` | `True` | Large paginated data |
| `validation_error()` | `False` | `False` | Parameter validation failures |

### `ValidationResult`

```python
@dataclass
class ValidationResult:
    success: bool                               # True = passed, False = failed
    param_name: str                             # Which parameter
    command_name: str                           # Which command
    message: str | None = None                  # Human-readable error
    suggested_value: str | None = None          # Auto-correction value
    valid_values: list[str] | None = None       # Allowed values (for LLM retry)
```

### `ReferenceableItem` and `@callback`

A command that reads out a list can let the user act on it in the next turn ("mark those as read", "send me number 3"). Return the items with `CommandResponse.with_items()`; each item's `actions` name methods decorated with `@callback` on the same command. The node remembers which command owns each item, and the built-in `act_on_items` tool calls the callback with the chosen rows.

```python
from jarvis_command_sdk import CommandResponse, ReferenceableItem, callback


def run(self, request_info, **kwargs) -> CommandResponse:
    items = [
        ReferenceableItem(ref_id=m.id, label=f"email from {m.sender}", actions=["mark_read"])
        for m in self._unread()
    ]
    return CommandResponse.with_items(f"You have {len(items)} unread emails.", items)

@callback("mark_read")
def mark_read(self, data: dict, request_info) -> CommandResponse:
    ...
```

`@callback` methods are also what a tap on a rich inbox item in the mobile app calls.

### `JarvisParameter`

See [Parameters Deep Dive](parameters.md).

### `JarvisSecret`

See [Secrets Deep Dive](secrets.md).

### `IJarvisButton`

```python
@dataclass
class IJarvisButton:
    button_text: str                            # "Send", "Cancel"
    button_action: str                          # "send_click", "cancel_click"
    button_type: Literal["primary", "secondary", "destructive"]
    button_icon: str | None = None              # MaterialCommunityIcons name
    completion_message: str | None = None       # Shown after the action succeeds ("Email sent!")
```

### `JarvisPackage`

```python
@dataclass(frozen=True)
class JarvisPackage:
    name: str                       # PyPI package name
    version: str | None = None      # Version spec or None for latest

    def to_pip_spec(self) -> str:
        """'requests', 'httpx==0.25.1', 'pydantic>=2.0,<3.0'"""

# Examples:
JarvisPackage("requests")                    # Latest
JarvisPackage("httpx", "0.25.1")             # Pinned
JarvisPackage("pydantic", ">=2.0,<3.0")     # Constraint
```

### `AuthenticationConfig`

See [OAuth Command Tutorial](tutorial-oauth.md) for full documentation. Key fields:

```python
@dataclass
class AuthenticationConfig:
    type: str                       # "oauth"
    provider: str                   # Groups commands sharing auth
    friendly_name: str              # Display name in mobile UI
    client_id: str                  # OAuth client ID
    keys: list[str]                 # Keys to extract from token response

    # External OAuth (full URLs):
    authorize_url: str | None = None       # "https://accounts.google.com/..."
    exchange_url: str | None = None        # "https://oauth2.googleapis.com/token"

    # Local/discoverable OAuth (paths + network scan):
    authorize_path: str | None = None      # "/auth/authorize"
    exchange_path: str | None = None       # "/auth/token"
    discovery_port: int | None = None      # 8123
    discovery_probe_path: str | None = None  # "/api/"

    # OAuth extras:
    scopes: list[str] = []
    extra_authorize_params: dict[str, str] = {}
    extra_exchange_params: dict[str, str] = {}
    send_redirect_uri_in_exchange: bool = True   # False for Home Assistant
    supports_pkce: bool = False
    client_secret: str | None = None  # Web-application clients: sent instead of PKCE
    native_redirect_uri: str | None = None

    # Background refresh:
    requires_background_refresh: bool = False
    refresh_interval_seconds: int = 600
    refresh_token_secret_key: str | None = None
```
