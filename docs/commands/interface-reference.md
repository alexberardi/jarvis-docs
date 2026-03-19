# Interface Reference

Complete reference for `IJarvisCommand` and all supporting classes. This is the authoritative guide to every property, method, and dataclass in the command system.

## Class Hierarchy

```
JarvisCommandBase (ABC)
  └── IJarvisCommand (ABC)
        └── YourCommand (concrete)
```

`JarvisCommandBase` provides the `execute()` orchestration (validation, auto-correction, then `run()`). `IJarvisCommand` adds the full property interface -- command name, description, parameters, secrets, examples, and all optional hooks.

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

Larger, more varied example set used for LoRA adapter training. Cover edge cases, alternative phrasings, and tricky inputs.

```python
def generate_adapter_examples(self) -> List[CommandExample]:
    return [
        CommandExample("What's the weather?", {}, is_primary=True),
        CommandExample("Do I need an umbrella?", {}),
        CommandExample("Weather in Miami", {"city": "Miami"}),
        # ... 20-40 examples covering variations
    ]
```

See [Examples & Training](examples.md) for best practices.

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

- `request_info`: A `RequestInformation` object with the original voice command, conversation ID, and validation context
- `**kwargs`: Validated parameters extracted by the LLM, matching your `parameters` definitions

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

### `required_packages -> List[JarvisPackage]`

Pip dependencies for this command. At install time, `install_command.py` collects all `required_packages` from enabled commands, checks for version conflicts against each other and against `requirements.txt`, and writes the merged result to `custom-requirements.txt`.

```python
from core.ijarvis_package import JarvisPackage

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
from core.ijarvis_authentication import AuthenticationConfig

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

---

## Lifecycle Methods

These methods participate in the command execution pipeline. See [Execution Lifecycle](lifecycle.md) for the full flow.

### `pre_route(voice_command) -> PreRouteResult | None`

Fast-path routing that bypasses the LLM entirely. Override for short, unambiguous utterances that can be parsed deterministically.

```python
def pre_route(self, voice_command: str) -> PreRouteResult | None:
    text = voice_command.lower().strip()
    if text in ("pause", "pause the music"):
        return PreRouteResult(arguments={"action": "pause"})
    return None  # Fall through to LLM
```

**Returns:** `PreRouteResult` with `arguments` dict and optional `spoken_response`, or `None` to use the normal LLM path.

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
from core.validation_result import ValidationResult

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

Handle interactive button taps from the mobile app. Called when a user taps a button on a response that included `actions`.

```python
from core.ijarvis_button import IJarvisButton

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

Called when OAuth tokens are delivered from the mobile app. Override to process and store tokens as secrets.

```python
def store_auth_values(self, values: dict[str, str]) -> None:
    from services.secret_service import set_secret
    if "access_token" in values:
        set_secret("GMAIL_ACCESS_TOKEN", values["access_token"], "integration")
    if "refresh_token" in values:
        set_secret("GMAIL_REFRESH_TOKEN", values["refresh_token"], "integration")
```

**Default:** No-op.

### `refresh_token() -> bool`

Refresh an OAuth2 access token. The default implementation POSTs to `auth.exchange_url` with `grant_type=refresh_token`, stores new tokens via `store_auth_values()`, and persists the expiration time.

Override for non-standard refresh flows.

**Default:** Standard OAuth2 refresh_token grant. Returns `True` on success, `False` on failure (and flags re-auth).

### `needs_auth() -> bool`

Check whether the mobile app should prompt the user for authentication.

**Default:** If `authentication` is declared, checks that all required secrets are present and that no re-auth flag is set in the `command_auth` table.

### `init_data() -> dict`

One-time initialization hook. Called manually via `python scripts/init_data.py --command <name>`. Use for first-install setup like registering devices or fetching initial state.

```python
def init_data(self) -> dict:
    # Fetch and cache initial device list
    devices = self._fetch_devices()
    return {"status": "success", "devices_found": len(devices)}
```

**Default:** Returns `{"status": "no_init_required"}`.

---

## The `execute()` Method (JarvisCommandBase)

You do not override `execute()` -- it is the orchestration method on `JarvisCommandBase` that calls your hooks in order:

```python
def execute(self, request_info, **kwargs) -> CommandResponse:
    self._validate_secrets()       # Check all required secrets present
    self._validate_params(kwargs)  # Check required params present
    results = self.validate_call(**kwargs)  # Value validation
    errors = [r for r in results if not r.success]
    if errors:
        return CommandResponse.validation_error(errors)
    for r in results:              # Apply auto-corrections
        if r.suggested_value is not None:
            kwargs[r.param_name] = r.suggested_value
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
```

### `CommandResponse`

See [Response Patterns](responses.md) for full documentation. Quick reference:

| Factory Method | Success | Wait for Input | Use Case |
|----------------|---------|----------------|----------|
| `success_response()` | `True` | `True` | Standard success |
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
```

### `JarvisPackage`

```python
@dataclass(frozen=True)
class JarvisPackage:
    name: str                       # PyPI package name
    version: str | None = None      # Version spec or None for latest

    def to_pip_spec(self) -> str:
        """'requests', 'httpx==0.25.1', 'pydantic>=2.0,<3.0'"""

    def to_requirement(self) -> Requirement:
        """Convert to a packaging.requirements.Requirement for programmatic use."""

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
    authorize_url: str | None       # "https://accounts.google.com/..."
    exchange_url: str | None        # "https://oauth2.googleapis.com/token"

    # Local/discoverable OAuth (paths + network scan):
    authorize_path: str | None      # "/auth/authorize"
    exchange_path: str | None       # "/auth/token"
    discovery_port: int | None      # 8123
    discovery_probe_path: str | None  # "/api/"

    # OAuth extras:
    scopes: list[str]
    extra_authorize_params: dict[str, str]
    extra_exchange_params: dict[str, str]
    supports_pkce: bool = False
    native_redirect_uri: str | None = None

    # Background refresh:
    requires_background_refresh: bool = False
    refresh_interval_seconds: int = 600
    refresh_token_secret_key: str | None = None
```
