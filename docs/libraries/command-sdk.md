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

For commands that expose structured data records to the mobile app, see [Data Browser Hooks](#data-browser-hooks). For commands that expose read-only, plan-time queries to server-side planners, see [Context Providers](#context-providers).

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

## Context Providers

Commands can declare typed, read-only queries that server-side planners (e.g. jarvis-command-center) can issue **at plan time only** — never during a live phone call, since the callee is untrusted input. Provider logic stays node-side so credentials never leave the node. Both hooks default to no-op/honest-failure, so existing commands are unaffected.

Requires **`jarvis-command-sdk >= 0.6.0`**.

### `IJarvisCommand.context_operations`

```python
@property
def context_operations(self) -> list[ContextOperation]:
    return []   # default
```

Commands override this to declare the operations they support.

### `IJarvisCommand.execute_context_operation(operation, params)`

```python
def execute_context_operation(
    self,
    operation: str,
    params: dict[str, Any],
) -> ContextResult:
    ...
```

Default implementation returns `ContextResult.failed(f"{command_name} does not implement '{operation}'")`.

### `ContextOperation`

```python
from jarvis_command_sdk import ContextOperation

ContextOperation(
    name: str,
    description: str,
    params_schema: dict[str, dict[str, Any]] = {},
    # flat map: {"param_name": {"type": str, "required": bool, "description": str}}
)
```

`to_dict()` → `{"name", "description", "params_schema"}`.  
`missing_required(params)` → list of required param names absent from `params`.

### `ContextResult`

```python
from jarvis_command_sdk import ContextResult

ContextResult(
    data: dict[str, Any] = {},
    error: str | None = None,
)
```

`ok` property is `True` iff `error is None`. `to_dict()` → `{"ok", "data", "error"}`. `ContextResult.failed(error: str)` classmethod builds a failed result. `data` must be JSON-serialisable — it crosses MQTT to reach the requesting planner.

### Example

```python
AVAILABILITY = ContextOperation(
    name="availability",
    description="Free/busy windows in a date range",
    params_schema={
        "start": {"type": "string", "required": True, "description": "ISO date"},
        "end": {"type": "string", "required": True, "description": "ISO date"},
        "granularity": {"type": "string", "required": False, "description": "…"},
    },
)

class CalendarCommand(IJarvisCommand):
    @property
    def context_operations(self):
        return [AVAILABILITY]

    def execute_context_operation(self, operation, params):
        if operation != "availability":
            return ContextResult.failed(f"unknown op {operation}")
        return ContextResult(data={"busy": [], "free": ["Thu 14:00-17:00"]})
```

See jarvis-node-setup's MQTT context-query handler and jarvis-command-center's `context_provider_client` for how planners discover and call providers over the wire.

## Changelog

| Version | What changed |
|---------|-------------|
| 0.6.0 | `context_operations`, `execute_context_operation`, `ContextOperation`, `ContextResult` — see [Context Providers](#context-providers) |
| 0.5.0 | `IJarvisDeviceProtocol.get_stream_source` optional async camera-streaming hook — see [Device Protocols](../extending/devices/protocols.md#get_stream_source--camera-streaming-hook-sdk-v050) |
| 0.4.1 | `data_browser_supports_create`, `data_browser_create`, `FieldSpec.create_only` |
| ≤ 0.3.x | `FieldSpec`, `JarvisStorage`, `data_browser_mode`, `display_summary` |
