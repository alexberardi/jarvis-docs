# jarvis-command-sdk

The `jarvis-command-sdk` Python package is the foundation for building Jarvis voice commands. It defines the `IJarvisCommand` interface that all Pantry-distributed and built-in commands implement, along with supporting types such as `FieldSpec` and `JarvisStorage`.

**Package:** `jarvis-command-sdk`  
**Current version:** `0.6.0`  
**Install:** `pip install jarvis-command-sdk`

## Core Interfaces

### `IJarvisCommand`

All commands extend `IJarvisCommand`. Required overrides:

| Method / property | Type | Notes |
|---|---|---|
| `command_name` | `str` (property) | Unique snake_case identifier |
| `description` | `str` (property) | One-line natural-language description for the LLM |
| `run(**kwargs)` | `CommandResponse` | Executes the command |

For commands that expose structured data records to the mobile app, see [Data Browser Hooks](#data-browser-hooks). For commands that expose typed, read-only queries to server-side planners, see [Context Provider Hooks](#context-provider-hooks).

### `FieldSpec`

Describes a single field in a command's data record. Used by the mobile data browser to render list, detail, edit, and create forms.

```python
from jarvis_command_sdk import FieldSpec

FieldSpec(
    name: str,
    type: str,               # "string" | "bool" | "int" | "datetime" | "date" | "time"
                             # | "array" | "enum" | "user_ref" | "id"
    label: str | None = None,
    description: str | None = None,
    editable: bool = True,
    create_only: bool = False,   # settable on create, read-only on edit (≥ 0.4.1)
    required: bool = False,
    enum_values: list[str] | None = None,
    item_type: str | None = None,  # element type for "array" fields
    fields: list[FieldSpec] | None = None,
    placeholder: str | None = None,
)
```

`FieldSpec.to_dict()` serialises for the MQTT/REST wire format; `FieldSpec.from_dict()` deserialises. Only non-default values appear on the wire.

### `JarvisStorage`

High-level persistence facade for Pantry-distributed commands. Wraps `CommandDataRepository` without importing node internals.

```python
from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("my_command")
storage.save("cache:Miami", {"temp": 75})
data = storage.get("cache:Miami")
all_data = storage.get_all()
```

See [Datastore](../extending/infrastructure/datastore.md#jarvisstorage-sdk-persistence-facade) for the full API.

### `IJarvisDeviceProtocol`

Interface for direct LAN/cloud device control plugins (LIFX, Kasa, Nest, etc.), including the optional `get_stream_source` camera-streaming hook added in 0.5.0. See [Device Protocols](../extending/devices/protocols.md) for the full interface and hook reference.

## Data Browser Hooks

Commands can opt into the mobile app's **Add Record** flow (the **+** FAB in the record list). The full protocol — including the node-side `_op_create` handler and MQTT wire format — is documented in [Data Browser Protocol](../extending/infrastructure/datastore.md#data-browser-protocol). This page covers the SDK surface.

Requires **`jarvis-command-sdk >= 0.4.1`**.

### `data_browser_supports_create`

```python
@property
def data_browser_supports_create(self) -> bool:
    return True   # default: False
```

When `True`, the node reports `"supports_create": true` in schema responses and the mobile app shows a **+** button in the record list.

The flag is opt-in: commands whose records carry runtime state that a generic save would bypass (e.g. an in-memory scheduler cache) must not enable create until `data_browser_create` routes through that state correctly.

### `data_browser_create(fields, requesting_user_id)`

```python
def data_browser_create(
    self,
    fields: dict[str, Any],
    requesting_user_id: int | None,
) -> tuple[str, dict]:
    ...
```

Called by the node when a `create` op arrives. `fields` is pre-filtered to **editable + `create_only`** field names; client-supplied `user_id`, `id`, and `created_at` are stripped before this hook is invoked.

Return `(data_key, record_dict)` on success. Raise `ValueError` with a user-readable message to reject the create — the node surfaces it as a 400 in the mobile app.

**Default implementation:** mints a UUID key, stamps `user_id = requesting_user_id`, persists via `JarvisStorage`, and fails closed (`ValueError`) when `requesting_user_id` is `None`. Override for domain-specific key shapes, validation, or scope rules.

### `FieldSpec.create_only`

```python
FieldSpec("scope", "enum",
          enum_values=["personal", "household"],
          editable=False,
          create_only=True)
```

Marks a field as settable at record creation but immutable on edit (e.g. record scope or ownership).

| | `editable` field | `create_only` field |
|---|---|---|
| Shown in create form | ✓ | ✓ (rendered editable) |
| Passed to `data_browser_create` | ✓ | ✓ |
| Patchable via update op | ✓ | ✗ (silently dropped) |
| Shown in edit form | ✓ | ✗ |

## Context Provider Hooks

Added in **`jarvis-command-sdk >= 0.6.0`** (jarvis-command-sdk#7). A command that holds live data (calendar events, device state, inventories) can declare **context operations** — typed, read-only queries that server-side planners (jarvis-command-center) invoke at **plan time**, before a plan is committed to. First consumer: the phone-call plan-draft step asks the calendar command for an `availability` operation so the confirm card carries a real constraint envelope instead of a fill-me-in placeholder. See [Command Center: Phone Calls](../services/command-center.md#phone-calls) for the caller side.

**Design rules:**

- **Plan-time only.** Context operations are never exposed as live tools inside a phone call or any other untrusted-counterparty loop — the callee on the other end of a call is untrusted input.
- **Read-only.** An operation must never mutate command state; mutations belong to commands/callbacks.
- **Node-side credentials.** The provider stays on the node; only the typed answer crosses the wire to command-center.
- **Honest failure, not raising.** Both hooks default to no-op — `context_operations` returns `[]`, and the base `execute_context_operation` returns a `ContextResult.failed(...)` naming the unimplemented operation. Raising is safe (the node runtime converts it to an error result) but returning `ContextResult.failed(...)` gives the planner a clearer message.

### `context_operations`

```python
@property
def context_operations(self) -> list[ContextOperation]:
    return []   # default: no context capability
```

Declares the typed queries this command can answer. Returns `[]` by default — most commands have nothing to add here.

### `execute_context_operation(operation, params)`

```python
def execute_context_operation(
    self, operation: str, params: dict[str, Any]
) -> ContextResult:
    ...
```

Answers one declared operation. Only called for operations present in `context_operations`; the node runtime validates required params (via `ContextOperation.missing_required`) before dispatching. The default implementation returns `ContextResult.failed(f"{self.command_name} does not implement '{operation}'")`.

### `ContextOperation`

```python
from jarvis_command_sdk import ContextOperation

ContextOperation(
    name: str,
    description: str,
    params_schema: dict[str, dict[str, Any]] = {},   # {param: {"type", "required", "description"}}
)
```

`params_schema` is deliberately a flat mapping rather than full JSON Schema — the node runtime validates required params before dispatching. `ContextOperation.missing_required(params)` returns the names of required params absent from a given call.

### `ContextResult`

```python
from jarvis_command_sdk import ContextResult

ContextResult(
    data: dict[str, Any] = {},
    error: str | None = None,
)
ContextResult.failed(error: str)   # convenience constructor, data={}
```

`ok` is `True` iff `error is None`. `data` must be JSON-serializable — it crosses MQTT to command-center. An `error` result is never fatal to the caller; planners are expected to degrade gracefully rather than block on a failed context query.

**Reference implementation:** `jarvis-cmd-calendar`'s `ReadCalendarCommand` is the first context provider, declaring an `availability` operation that derives free/busy windows from the speaker's calendar (requires `jarvis-command-sdk >= 0.6.0`). See its row in [Pantry-Installable Commands](../commands/index.md#pantry-installable-commands).

## Changelog

| Version | What changed |
|---------|-------------|
| 0.6.0 | `context_operations`, `execute_context_operation`, `ContextOperation`, `ContextResult` — context-provider capability (typed plan-time queries) — see [Context Provider Hooks](#context-provider-hooks) |
| 0.5.0 | `IJarvisDeviceProtocol.get_stream_source` optional async camera-streaming hook — see [Device Protocols](../extending/devices/protocols.md#get_stream_source--camera-streaming-hook-sdk-v050) |
| 0.4.1 | `data_browser_supports_create`, `data_browser_create`, `FieldSpec.create_only` |
| ≤ 0.3.x | `FieldSpec`, `JarvisStorage`, `data_browser_mode`, `display_summary` |
