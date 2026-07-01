# jarvis-command-sdk

The `jarvis-command-sdk` Python package is the foundation for building Jarvis voice commands. It defines the `IJarvisCommand` interface that all Pantry-distributed and built-in commands implement, along with supporting types such as `FieldSpec` and `JarvisStorage`.

**Package:** `jarvis-command-sdk`  
**Current version:** `0.4.1`  
**Install:** `pip install jarvis-command-sdk`

## Core Interfaces

### `IJarvisCommand`

All commands extend `IJarvisCommand`. Required overrides:

| Method / property | Type | Notes |
|---|---|---|
| `command_name` | `str` (property) | Unique snake_case identifier |
| `description` | `str` (property) | One-line natural-language description for the LLM |
| `run(**kwargs)` | `CommandResponse` | Executes the command |

For commands that expose structured data records to the mobile app, see [Data Browser Hooks](#data-browser-hooks).

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
storage.set("cache:Miami", {"temp": 75})
data = storage.get("cache:Miami")
all_data = storage.get_all()
```

See [Datastore](../extending/infrastructure/datastore.md#jarvisstorage-sdk-persistence-facade) for the full API.

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

## Changelog

| Version | What changed |
|---------|-------------|
| 0.4.1 | `data_browser_supports_create`, `data_browser_create`, `FieldSpec.create_only` |
| ≤ 0.3.x | `FieldSpec`, `JarvisStorage`, `data_browser_mode`, `display_summary` |
