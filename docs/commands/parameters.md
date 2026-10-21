# Parameters Deep Dive

Parameters define what data your command accepts from the LLM. They are declared as `JarvisParameter` objects in your command's `parameters` property, converted to JSON Schema for the LLM's tool interface, and validated by the execution pipeline before `run()` is called.

## JarvisParameter Constructor

```python
JarvisParameter(
    name: str,                          # Parameter name (snake_case)
    param_type: str,                    # Type string (see table below)
    required: bool = False,             # Whether the LLM must provide this
    description: str | None = None,     # Description shown to the LLM
    default: str | None = None,         # Default value
    enum_values: list[str] | None = None,  # Constrained values
    refinable: bool = False,            # Filled in by a second, focused model call (see below)
    options_source: str | None = None,  # Live option list for UIs (see below)
)
```

`JarvisParameter` is imported from `jarvis_command_sdk`.

`options_source` tells UIs such as the routine builder to fill a dropdown from live data instead of (or as well as) `enum_values`: `"devices"`, `"devices:<domain>"` (e.g. `"devices:light"`), `"rooms"` or `"news_categories"`. It is copied into the parameter's tool schema as `options_source`.

## Supported Types

### Primitive Types

| Type String | Aliases | JSON Schema Type | Python Type |
|-------------|---------|------------------|-------------|
| `"string"` | `"str"` | `string` | `str` |
| `"integer"` | `"int"` | `integer` | `int` |
| `"float"` | | `number` | `float` |
| `"boolean"` | `"bool"` | `boolean` | `bool` |
| `"array"` | `"list"` | `array` | `list` |
| `"dict"` | | `object` | `dict` |

### Datetime Types

| Type String | JSON Schema Type | Python Type |
|-------------|------------------|-------------|
| `"datetime"` | `string` | `datetime.datetime` |
| `"date"` | `string` | `datetime.date` |
| `"time"` | `string` | `datetime.time` |
| `"timedelta"` | `string` | `datetime.timedelta` |

### Image Type

| Type String | Aliases | What `run()` receives |
|-------------|---------|------------------------|
| `"image"` | `"array<image>"` | `list[JarvisImage]` |

An image parameter receives the photos the user attached in the mobile app's chat: always a list, in attach order, at most 4 images of at most 2 MiB each. `execute()` turns the wire value into `JarvisImage` objects before `validate_call()`; a bad image, or an empty list for a required parameter, comes back as a validation error.

### Array Types

The date and time arrays accept three spellings; the other arrays only the angle-bracket one:

| Angle Bracket | Square Bracket | Shorthand | `items` in the tool schema |
|--------------|----------------|-----------|------------|
| `"array<datetime>"` | `"array[datetime]"` | `"datetime[]"` | `{"type": "string", "format": "date-time"}` |
| `"array<date>"` | `"array[date]"` | `"date[]"` | `{"type": "string", "format": "date"}` |
| `"array<time>"` | `"array[time]"` | `"time[]"` | none |
| `"array<timedelta>"` | `"array[timedelta]"` | `"timedelta[]"` | none |
| `"array<string>"` | | | none |
| `"array<int>"` | | | none |
| `"array<float>"` | | | none |
| `"array<bool>"` | | | none |

The tool schema describes only `datetime` and `date` arrays' items; every other array reaches the model as a bare `"type": "array"`, so say what the items are in the `description`.

**Example -- weather command with date array:**

```python
JarvisParameter(
    "resolved_datetimes",
    "array<datetime>",
    required=True,
    description="Date keys: 'today', 'tomorrow', 'this_weekend', etc.",
)
```

Using an invalid type string raises a `ValueError` at class instantiation time.

## Required vs. Optional

```python
# Required -- LLM must extract this from the voice command
JarvisParameter("ticker", "string", required=True, description="Stock symbol")

# Optional with default -- LLM may omit, code uses default
JarvisParameter("count", "int", required=False, default="1", description="Number of dice")

# Optional without default -- LLM may omit, code checks for None
JarvisParameter("city", "string", required=False, description="City name. Omit for default.")
```

If a required parameter is missing, the execution pipeline raises a `ValueError` before `run()` is called.

## Enum Values

Constrain a parameter to a fixed set of values:

```python
JarvisParameter(
    "operation",
    "string",
    required=True,
    description="Arithmetic operation to perform",
    enum_values=["add", "subtract", "multiply", "divide"],
)
```

The LLM sees these as an `enum` in the JSON Schema. During validation, if the value does not match any enum value, a `ValidationResult` error is generated with the list of valid values. The node sends that back to `jarvisd` as a failed tool result, and the model can call the tool again with a valid value.

**Enum values are always strings**, even for integer parameters. Compare as strings when validating.

### Dynamic Enums

For values that come from runtime data (like device names), use `validate_call()` instead of static `enum_values`:

```python
@property
def parameters(self) -> List[JarvisParameter]:
    return [
        JarvisParameter("action", "string", required=True, enum_values=[
            "turn_on", "turn_off", "lock", "unlock",
        ]),
        # entity_id has no static enum -- validated dynamically
        JarvisParameter("entity_id", "string", required=False),
    ]

def validate_call(self, **kwargs) -> list[ValidationResult]:
    results = super().validate_call(**kwargs)
    entity_id = kwargs.get("entity_id")
    if entity_id:
        known = self._get_known_entities()
        if entity_id not in known:
            results.append(ValidationResult(
                success=False,
                param_name="entity_id",
                command_name=self.command_name,
                message=f"Device '{entity_id}' not found",
                valid_values=known,
            ))
    return results
```

## The `refinable` Flag

A `refinable` parameter is left out of the first tool call and filled in by a second, focused model call. Use it for detail parameters that a small model tends to get wrong when it also has to pick the tool.

```python
JarvisParameter(
    "volume_level",
    "int",
    required=False,
    description="Volume level 0-100",
    refinable=True,
)

JarvisParameter(
    "queue_option",
    "string",
    required=False,
    enum_values=["play", "next", "add"],
    description="Queue behavior",
    refinable=True,
)
```

When `refinable=True`, the parameter schema includes a `_refinable: true` marker. On the text path, `jarvisd` removes refinable parameters from the schema the model sees when it picks the tool. Once the model has picked this tool, `jarvisd` makes a second, focused model call on the same utterance to fill in the refinable parameters, and adds them to the tool call before it goes to the node. `control_device` and `get_device_status` have their own resolvers and skip this step. It applies to the current utterance only; follow-up turns ("make it louder") are ordinary new turns.

## Validation Pipeline

Parameters go through three layers of validation in the `execute()` pipeline:

### 1. Presence Validation (in `execute()`)

Checks that all `required=True` parameters are present in kwargs. If any are missing, raises `ValueError`.

### 2. Type Validation (`param.validate()` -> `_validate_type`)

Checks that the value matches the declared type:

```python
# These pass type validation:
JarvisParameter("count", "int")     # value=5 -> OK
JarvisParameter("ratio", "float")   # value=3 (int) -> OK (int accepted for float)
JarvisParameter("dates", "array<datetime>")  # value=["2025-01-01"] -> OK (is a list)

# These fail:
JarvisParameter("count", "int")     # value="five" -> FAIL
JarvisParameter("flag", "bool")     # value="yes" -> FAIL
```

### 3. Enum Validation

If `enum_values` is set, checks that `str(value)` is in the list:

```python
JarvisParameter("op", "string", enum_values=["add", "subtract"])
# value="add"      -> OK
# value="multiply" -> FAIL: "Invalid value 'multiply' for 'op'. Must be one of: add, subtract"
```

### 4. Custom Validation Function

The `IJarvisParameter` abstract class supports a `validation_function` property for custom inline validation. When using `JarvisParameter` directly, use `validate_call()` on the command instead.

```python
# On the abstract IJarvisParameter:
@property
def validation_function(self) -> Callable[[Any], bool] | None:
    return lambda v: 0 <= v <= 100

@property
def validation_error_message(self) -> str:
    return "Value must be between 0 and 100"
```

## How Parameters Become Tool Schema

Your parameters are converted to JSON Schema for the LLM via `to_openai_tool_schema()`:

```python
# Given these parameters:
parameters = [
    JarvisParameter("city", "string", required=False, description="City name"),
    JarvisParameter("unit", "string", required=False, enum_values=["metric", "imperial"]),
    JarvisParameter("dates", "array<datetime>", required=True, description="Target dates"),
]

# to_openai_tool_schema() returns:
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Weather conditions or forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                },
                "unit": {
                    "type": "string",
                    "enum": ["metric", "imperial"]
                },
                "dates": {
                    "type": "array",
                    "description": "Target dates",
                    "items": {"type": "string", "format": "date-time"}
                }
            },
            "required": ["dates"]
        }
    },
    "allow_direct_answer": false,
    "is_risky": false,
    "keywords": [...],
    "examples": [...]
}
```

The top-level `allow_direct_answer`, `is_risky`, `keywords`, `examples` (and `antipatterns`, when declared) are Jarvis extensions, read by `jarvisd` when it builds the prompt. Where it passes the tools on as tool definitions, it removes `allow_direct_answer`, `keywords`, `examples` and the `_refinable` markers first.

## Best Practices

1. **Use descriptive names** -- `city` not `c`, `volume_level` not `vol`
2. **Write clear descriptions** -- this is the primary way the LLM knows what to extract
3. **Make parameters optional when possible** -- with sensible defaults in `run()`
4. **Use enums for constrained values** -- reduces LLM errors significantly
5. **Keep parameter count low** -- 1-5 parameters is ideal. More than 7 confuses smaller models.
6. **Use `critical_rules` for mapping guidance** -- when voice words do not match parameter values (e.g., "plus" -> "add")
7. **Guard against LLM artifacts in `run()`** -- check for literal strings like `"default"`, `"none"`, `"null"` that the LLM might pass instead of omitting the parameter
