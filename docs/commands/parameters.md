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
    refinable: bool = False,            # Can be refined by the user after initial response
)
```

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

### Array Types

Array types use three equivalent syntaxes:

| Angle Bracket | Square Bracket | Shorthand | Items Type |
|--------------|----------------|-----------|------------|
| `"array<datetime>"` | `"array[datetime]"` | `"datetime[]"` | `date-time` |
| `"array<date>"` | `"array[date]"` | `"date[]"` | `date` |
| `"array<time>"` | `"array[time]"` | `"time[]"` | `time` |
| `"array<timedelta>"` | `"array[timedelta]"` | `"timedelta[]"` | `timedelta` |
| `"array<string>"` | `"array[string]"` | | `string` |
| `"array<int>"` | `"array[int]"` | | `integer` |
| `"array<float>"` | `"array[float]"` | | `number` |
| `"array<bool>"` | `"array[bool]"` | | `boolean` |

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

The LLM sees these as an `enum` in the JSON Schema. During validation, if the value does not match any enum value, a `ValidationResult` error is generated with the list of valid values. The command center can then retry with the corrected value.

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

A `refinable` parameter can be adjusted by the user after the initial response, without restarting the command. This is used for parameters where the user might want to tweak the value.

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

When `refinable=True`, the parameter schema includes a `_refinable: true` hint. This signals to the command center that follow-up utterances like "make it louder" or "actually, play it next" should be interpreted as parameter refinements rather than new commands.

## Validation Pipeline

Parameters go through three layers of validation in the `execute()` pipeline:

### 1. Presence Validation (`_validate_params`)

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

# The LLM sees this schema:
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
    }
}
```

## Best Practices

1. **Use descriptive names** -- `city` not `c`, `volume_level` not `vol`
2. **Write clear descriptions** -- this is the primary way the LLM knows what to extract
3. **Make parameters optional when possible** -- with sensible defaults in `run()`
4. **Use enums for constrained values** -- reduces LLM errors significantly
5. **Keep parameter count low** -- 1-5 parameters is ideal. More than 7 confuses smaller models.
6. **Use `critical_rules` for mapping guidance** -- when voice words do not match parameter values (e.g., "plus" -> "add")
7. **Guard against LLM artifacts in `run()`** -- check for literal strings like `"default"`, `"none"`, `"null"` that the LLM might pass instead of omitting the parameter
