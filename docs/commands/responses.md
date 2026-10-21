# Response Patterns

`CommandResponse` is the return type of every `run()` method (import it from `jarvis_command_sdk`). The node turns it into a tool result and posts it to `jarvisd`, whose model writes the spoken reply from it.

## CommandResponse Structure

```python
@dataclass
class CommandResponse:
    context_data: dict | None = None       # Raw data for the LLM to generate a spoken response
    success: bool = True                   # Whether the command succeeded
    error_details: str | None = None       # Error message (sets success=False automatically)
    wait_for_input: bool = True            # Whether to keep the conversation open
    clear_history: bool = False            # Clear conversation history before next turn
    metadata: dict | None = None           # Command-specific metadata
    actions: list[IJarvisButton] | None = None  # Interactive buttons
    referenceable_items: list[ReferenceableItem] | None = None  # Items the user can act on next
    is_chunked_response: bool = False      # Chunked response flag
    chunk_session_id: str | None = None    # Session ID for chunked responses
    on_response_complete: Callable[[], None] | None = None  # Run after the reply is spoken (node only)
```

What the node sends to `jarvisd` for each tool call is `success`, `message` (taken out of `context_data` and put first), the rest of `context_data` as `context` (with `actions`), `error` and `referenceable_items`. `metadata`, `wait_for_input`, `clear_history` and `on_response_complete` stay on the node.

## Factory Methods

### `success_response()` -- Standard Success

The most common response. The conversation stays open for follow-up by default.

```python
return CommandResponse.success_response(
    context_data={
        "city": "Chicago",
        "temperature": 72,
        "description": "partly cloudy",
        "message": "It's 72 degrees and partly cloudy in Chicago",
    }
)
```

The LLM uses `context_data` to generate a natural spoken response. Include a `message` key with what to say, plus structured data. When `message` is spoken word for word, see [`context_data` Best Practices](#context_data-best-practices).

**Signature:**

```python
CommandResponse.success_response(
    context_data: dict | None = None,
    wait_for_input: bool = True,
    metadata: dict | None = None,
    on_response_complete: Callable[[], None] | None = None,
) -> CommandResponse
```

`on_response_complete` is for media commands: the node calls it after the spoken reply has finished, so playback starts once the speaker is free. Do the searching in `run()` and only start the audio in the callback.

### `with_items()` -- A List the User Can Act On

Use it when the command reads out a list the user may refer back to ("mark those as read", "send me number 3"). `message` is spoken and `items` are remembered for the rest of the conversation:

```python
return CommandResponse.with_items(
    "You have 2 unread emails: from ABC about the invoice, and from Sam.",
    [
        ReferenceableItem(ref_id="msg-1", label="email from ABC - 'Invoice #42'", actions=["mark_read"]),
        ReferenceableItem(ref_id="msg-2", label="email from Sam", actions=["mark_read"]),
    ],
)
```

Each item's `actions` must name `@callback` methods on the same command; the built-in `act_on_items` tool calls them. See [Interface Reference](interface-reference.md#referenceableitem-and-callback).

**Signature:**

```python
CommandResponse.with_items(
    message: str,
    items: list[ReferenceableItem],
    *,
    context_data: dict | None = None,
    wait_for_input: bool = True,
    metadata: dict | None = None,
) -> CommandResponse
```

### `error_response()` -- Errors

Return when the command fails. The conversation closes by default.

```python
return CommandResponse.error_response(
    error_details="OpenWeather API key is not configured",
    context_data={"error": "missing_api_key"},
)
```

**Signature:**

```python
CommandResponse.error_response(
    error_details: str,
    context_data: dict | None = None,
    wait_for_input: bool = False,
) -> CommandResponse
```

**Tips:**

- `error_details` is a human-friendly message that the LLM uses to generate a spoken error
- Include `context_data` for debugging even in errors
- Set `wait_for_input=True` if the user can retry (e.g., "City not found, try a different one")

### `follow_up_response()` -- Expects More Input

Return when the command succeeds but expects the user to continue the conversation. Used by the calculator (for chained calculations), chat, and other interactive commands.

```python
return CommandResponse.follow_up_response(
    context_data={
        "result": 42,
        "calculation": "6 * 7 = 42",
        "message": "6 times 7 equals 42",
    }
)
```

The conversation stays open. The user can say "now multiply that by 2"; the model sees the earlier turn and can call the same command again.

**Signature:**

```python
CommandResponse.follow_up_response(
    context_data: dict,
    metadata: dict | None = None,
) -> CommandResponse
```

### `final_response()` -- One-Shot, No Follow-Up

Return when the command is done and no follow-up is expected. The conversation ends.

```python
return CommandResponse.final_response(
    context_data={
        "message": "Timer set for 5 minutes",
        "timer_id": "abc123",
        "duration_seconds": 300,
    }
)
```

**Signature:**

```python
CommandResponse.final_response(
    context_data: dict | None = None,
    metadata: dict | None = None,
) -> CommandResponse
```

### `chunked_response()` -- Large Data

Return when the response is too large for a single message. The user can ask for more with follow-up commands like "continue" or "next page".

```python
return CommandResponse.chunked_response(
    session_id="news-session-abc123",
    context_data={
        "headlines": headlines[:5],
        "total": len(headlines),
        "message": f"Here are the top 5 of {len(headlines)} headlines. Say 'more' for the next batch.",
    }
)
```

**Signature:**

```python
CommandResponse.chunked_response(
    session_id: str,
    context_data: dict | None = None,
    metadata: dict | None = None,
) -> CommandResponse
```

The `session_id` is used to track the chunked session across turns. On the next turn, the command can use the session ID to resume from where it left off.

### `validation_error()` -- Parameter Validation Failures

Returned automatically by the `execute()` pipeline when `validate_call()` produces errors. You rarely call this directly -- it is generated for you.

```python
return CommandResponse.validation_error([
    ValidationResult(
        success=False,
        param_name="entity_id",
        command_name="control_device",
        message="Device 'light.nonexistent' not found",
        valid_values=["light.living_room", "light.kitchen", "light.bedroom"],
    ),
])
```

The node sends this to `jarvisd` as an ordinary failed tool result. The model can then:

- call the tool again with a value from `valid_values` (if it repeats exactly the same call, the node stops and the user hears the error)
- ask the user to clarify, through `jarvisd`'s `request_validation` tool

**Signature:**

```python
CommandResponse.validation_error(
    results: list[ValidationResult],
) -> CommandResponse
```

## Choosing the Right Response

| Scenario | Factory Method | `wait_for_input` |
|----------|---------------|------------------|
| Weather report | `success_response()` | `True` |
| Calculator result | `follow_up_response()` | `True` |
| Timer set | `final_response()` | `False` |
| Music playing | `success_response(wait_for_input=False)` | `False` |
| API error | `error_response()` | `False` |
| News with pagination | `chunked_response()` | `True` |
| Bad device name | `validation_error()` | `False` |
| Email sent | `final_response()` | `False` |
| Email draft preview | Response with `actions` | `True` |

## Interactive Actions with IJarvisButton

Attach buttons to a response for interactive flows. The mobile app renders these as tappable buttons.

```python
from jarvis_command_sdk import CommandResponse, IJarvisButton

return CommandResponse(
    context_data={
        "draft": {
            "to": "alice@example.com",
            "subject": "Meeting tomorrow",
            "body": "Hi Alice, are we still on for tomorrow?",
        },
        "message": "Here's your email draft to Alice. Send it or cancel?",
    },
    success=True,
    wait_for_input=True,
    actions=[
        IJarvisButton(
            button_text="Send",
            button_action="send_click",
            button_type="primary",
            button_icon="send",
        ),
        IJarvisButton(
            button_text="Cancel",
            button_action="cancel_click",
            button_type="destructive",
            button_icon="close",
        ),
    ],
)
```

### Button Types

| Type | Appearance | Use Case |
|------|------------|----------|
| `"primary"` | Highlighted / accent color | Main action (Send, Confirm) |
| `"secondary"` | Neutral | Alternative action (Edit, Save Draft) |
| `"destructive"` | Red / warning | Dangerous action (Delete, Cancel) |

### Button Icons

Use [MaterialCommunityIcons](https://pictogrammers.com/library/mdi/) names:

```python
IJarvisButton("Send", "send_click", "primary", button_icon="send")
IJarvisButton("Edit", "edit_click", "secondary", button_icon="pencil")
IJarvisButton("Delete", "delete_click", "destructive", button_icon="delete")
```

## Handling Button Actions

When the user taps a button, `jarvisd` forwards the tap to the node over MQTT. The node calls your command's `handle_action()` method and posts the result back:

```python
def handle_action(self, action_name: str, context: dict) -> CommandResponse:
    if action_name == "send_click":
        draft = context.get("draft", {})
        self._send_email(
            to=draft["to"],
            subject=draft["subject"],
            body=draft["body"],
        )
        return CommandResponse.final_response(
            context_data={"message": "Email sent successfully."}
        )

    # The base class handles "cancel_click" automatically
    return super().handle_action(action_name, context)
```

The `context` dict contains the `context_data` from the original response. This is how you pass data from the preview to the action handler (e.g., the email draft).

### Default `cancel_click` Handler

The base class provides a default handler for `cancel_click`:

```python
# Built-in on IJarvisCommand -- no need to implement
if action_name == "cancel_click":
    return CommandResponse.final_response(
        context_data={"cancelled": True, "message": "Cancelled."}
    )
```

## `context_data` Best Practices

`context_data` is the bridge between your command and the spoken response. The node puts `message` at the top of the tool result, and `jarvisd`'s model reads the result and writes the reply.

### Always include a `message` key

```python
context_data={
    "temperature": 72,
    "city": "Chicago",
    "message": "It's 72 degrees in Chicago",  # LLM uses this as a starting point
}
```

Sometimes `message` is spoken exactly as you wrote it, with no model in between:

- **On the fast path** (`request_info.is_pre_routed` is `True`): no model is involved, so `message` (or the `PreRouteResult`'s `spoken_response`) is the reply.
- **When the response keeps the conversation open** (`wait_for_input=True`) and succeeded: the node speaks the command's own `message` instead of the model's reply, because small models misread state data. With `wait_for_input=False` the model's reply is spoken.

So write `message` as a complete sentence you are happy to hear.

### Include structured data for the mobile UI

```python
context_data={
    "emails": [
        {"from": "alice@example.com", "subject": "Meeting", "snippet": "..."},
        {"from": "bob@example.com", "subject": "Lunch?", "snippet": "..."},
    ],
    "total": 5,
    "message": "You have 5 unread emails. The first is from Alice about Meeting.",
}
```

### Keep error context helpful

```python
# Good -- gives the LLM context to explain the problem
context_data={
    "ticker": "INVALID",
    "error": "not_found",
    "message": "I couldn't find a stock with ticker 'INVALID'",
}

# Bad -- no context
context_data=None
```

## The `metadata` Field

`metadata` is for command-internal data that should not influence the spoken response. It stays on the node: it is not sent to `jarvisd` or shown to the LLM.

```python
return CommandResponse.success_response(
    context_data={"message": "Timer set for 5 minutes"},
    metadata={
        "timer_id": "internal-uuid",
        "created_at": "2025-01-01T12:00:00Z",
        "node_id": "abc123",
    },
)
```

## The `clear_history` Flag

Set `clear_history=True` to reset the conversation context before the next turn. Useful when a command fundamentally changes the conversation state:

```python
return CommandResponse(
    context_data={"message": "Starting a new conversation"},
    success=True,
    clear_history=True,
)
```
